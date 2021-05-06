from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import (QUrl, QEventLoop, QTimer, QUrlQuery,
                              QObject, pyqtSignal)
import json


class Reply:
    '''
    wrapper of qnetworkreply to match interface of requests library
    '''
    def __init__(self, reply: QNetworkReply):
        '''
        Parameters
        ----------
        reply : QNetworkReply
            the reply of a QNetworkRequest to wrap
        '''
        self.reply = reply
        # streamed
        if hasattr(reply, 'readAll'):
            self.raw_data = reply.readAll()
        # reply received with blocking call
        else:
            self.raw_data = reply.content()

    @property
    def url(self) -> str:
        '''
        Returns
        ----------
        str
            the requested URL
        '''
        return self.reply.url().url()

    @property
    def status_code(self) -> int:
        '''
        Returns
        ----------
        int
            the HTML status code returned by the requested server
        '''
        return self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

    @property
    def content(self) -> str:
        '''
        Returns
        ----------
        str
            the response of the server
        '''
        return self.raw_data.data()

    def raise_for_status(self):
        '''
        raise error when request was not successful
        '''
        if self.status_code != 200:
            raise ConnectionError(self.status_code)

    def json(self) -> dict:
        '''
        parse response into a json object

        Returns
        ----------
        dict
            the response as a json-style dictionary
        '''
        return json.loads(self.content)

    @property
    def headers(self) -> dict:
        '''
        Returns
        ----------
        dict
            the headers of the response
        '''
        headers = {}
        for h in ['ContentDispositionHeader', 'ContentTypeHeader',
                  'LastModifiedHeader', 'ContentLengthHeader',
                  'CookieHeader', 'LocationHeader',
                  'UserAgentHeader', 'LocationHeader']:
            headers[h] = self.reply.header(getattr(QNetworkRequest, h))
        return headers


class Request(QObject):
    '''
    Wrapper of QgsNetworkAccessManager to match interface of requests library,
    can make synchronous or asynchronous calls

    ensures compatibility of synchronous requests with QGIS versions prior 3.6

    Attributes
    ----------
    finished : pyqtSignal
        emitted when the request is done and the server responded, Reply
    error : pyqtSignal
        emitted on error, error message
    progress : pyqtSignal
        emitted on progress, percentage of progress
    '''
    finished = pyqtSignal(Reply)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, synchronous: bool = False):
        '''
        Parameters
        ----------
        synchronous : bool, optional
            requests are made either synchronous (True) or asynchronous (False),
            defaults to synchronous calls
        '''
        super().__init__()
        self.synchronous = synchronous

    @property
    def _manager(self) -> QgsNetworkAccessManager:
        return QgsNetworkAccessManager.instance()

    def get(self, url: str, params: dict = None,
            timeout: int = 10000, **kwargs) -> Reply:
        '''
        queries given url (GET)

        Parameters
        ----------
        url : str
            the url to request
        params : dict, optional
            query parameters with the parameters as keys and the values as
            values, defaults to no query parameters
        timeout : int, optional
            the timeout of synchronous requests in milliseconds, will be ignored
            when making asynchronous requests, defaults to 10000 ms
        **kwargs :
            additional parameters matching the requests interface will
            be ignored (e.g. verify is not supported)

        Returns
        ----------
        Reply
           the response is returned in case of synchronous calls, if you are
           using asynchronous calls retrieve the response via the finished-
           signal instead
        '''
        qurl = QUrl(url)

        if params:
            query = QUrlQuery()
            for param, value in params.items():
                query.addQueryItem(param, str(value))
            qurl.setQuery(query.query())

        if self.synchronous:
            return self._get_sync(qurl, timeout=timeout)

        return self._get_async(qurl)

    def post(self, url, params: dict = None, data: bytes = b'',
             timeout: int = 10000, **kwargs) -> Reply:
        '''
        posts data to given url (POST)

        asynchronous posts are not implemented yet

        Parameters
        ----------
        url : str
            the url to post to
        params : dict, optional
            query parameters with the parameters as keys and the values as
            values, defaults to no query parameters
        data : bytes, optional
            the data to post as a byte-string, defaults to no data posted
        timeout : int, optional
            the timeout of synchronous requests in milliseconds, will be ignored
            when making asynchronous requests, defaults to 10000 ms
        **kwargs :
            additional parameters matching the requests-interface will
            be ignored (e.g. verify is not supported)

        Returns
        ----------
        Reply
           the response is returned in case of synchronous calls, if you are
           using asynchronous calls retrieve the response via the finished-
           signal instead
        '''
        qurl = QUrl(url)

        if params:
            query = QUrlQuery()
            for param, value in params.items():
                query.addQueryItem(param, str(value))
            qurl.setQuery(query.query())

        if self.synchronous:
            return self._post_sync(qurl, timeout=timeout, data=data)

        return self._post_async(qurl)


    def _get_sync(self, qurl: QUrl, timeout: int = 10000) -> Reply:
        '''
        synchronous GET-request
        '''
        request = QNetworkRequest(qurl)
        # newer versions of QGIS (3.6+) support synchronous requests
        if hasattr(self._manager, 'blockingGet'):
            reply = self._manager.blockingGet(request, forceRefresh=True)
        # use blocking event loop for older versions
        else:
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            # reply or timeout break event loop, whoever comes first
            timer.timeout.connect(loop.quit)
            reply = self._manager.get(request)
            reply.finished.connect(loop.quit)

            timer.start(timeout)

            # start blocking loop
            loop.exec()
            loop.deleteLater()
            if not timer.isActive():
                reply.deleteLater()
                raise ConnectionError('Timeout ')

            timer.stop()
        if reply.error():
            self.error.emit(reply.errorString())
            raise ConnectionError(reply.errorString())
        res = Reply(reply)
        self.finished.emit(res)
        return res

    def _get_async(self, qurl: QUrl):
        '''
        asynchronous GET-request
        '''
        request = QNetworkRequest(qurl)

        def progress(b, total):
            if total > 0:
                self.progress.emit(int(100*b/total))

        self.reply = self._manager.get(request)
        self.reply.error.connect(
            lambda: self.error.emit(self.reply.errorString()))
        self.reply.downloadProgress.connect(progress)
        self.reply.finished.connect(
            lambda: self.finished.emit(Reply(self.reply)))
        #self.reply.readyRead.connect(ready_read)
        #return 0

    def _post_sync(self, qurl: QUrl, timeout: int = 10000, data: bytes = b''):
        '''
        synchronous POST-request
        '''
        request = QNetworkRequest(qurl)
        # newer versions of QGIS (3.6+) support synchronous requests
        if hasattr(self._manager, 'blockingPost'):
            reply = self._manager.blockingPost(request, data, forceRefresh=True)
        # use blocking event loop for older versions
        else:
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            # reply or timeout break event loop, whoever comes first
            timer.timeout.connect(loop.quit)
            reply = self._manager.post(request, data)
            reply.finished.connect(loop.quit)

            timer.start(timeout)

            # start blocking loop
            loop.exec()
            loop.deleteLater()
            if not timer.isActive():
                reply.deleteLater()
                raise ConnectionError('Timeout ')

            timer.stop()
        if reply.error():
            self.error.emit(reply.errorString())
        res = Reply(reply)
        self.finished.emit(res)
        return res

    def _post_async(self, qurl: QUrl):
        '''
        asynchronous POST-request

        not implemented yet
        '''
        raise NotImplementedError

