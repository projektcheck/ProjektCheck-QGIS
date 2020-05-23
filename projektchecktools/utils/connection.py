from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import (QUrl, QEventLoop, QTimer, QUrlQuery,
                              QObject, pyqtSignal)
import json


class Reply:
    def __init__(self, reply):
        '''
        reply - qnetworkreply
        '''
        self.reply = reply
        # streamed
        if hasattr(reply, 'readAll'):
            self.raw_data = reply.readAll()
        # reply received with blocking call
        else:
            self.raw_data = reply.content()

    @property
    def url(self):
        return self.reply.url().url()

    @property
    def status_code(self):
        return self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

    @property
    def content(self):
        return self.raw_data.data()

    def raise_for_status(self):
        if self.status_code != 200:
            raise ConnectionError(self.status_code)

    def json(self):
        return json.loads(self.content)

    @property
    def headers(self):
        headers = {}
        for h in ['ContentDispositionHeader', 'ContentTypeHeader',
                  'LastModifiedHeader', 'ContentLengthHeader',
                  'CookieHeader', 'LocationHeader',
                  'UserAgentHeader', 'LocationHeader']:
            headers[h] = self.reply.header(getattr(QNetworkRequest, h))
        return headers


class Request(QObject):
    finished = pyqtSignal(Reply)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, synchronous=False):
        super().__init__()
        self.synchronous = synchronous
        self.manager = QgsNetworkAccessManager.instance()

    def get(self, url, params=None, timeout=10000, verify=False):
        '''
        timeout only relevant for synchronous calls
        ToDo: verify actually doesn't do anything, just to match requests api
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

    def _get_sync(self, qurl: QUrl, timeout=10000):
        request = QNetworkRequest(qurl)
        # newer versions of QGIS (3.6+) support synchronous requests
        if hasattr(self.manager, 'blockingGet'):
            reply = self.manager.blockingGet(request, forceRefresh=True)
        # use blocking event loop for older versions
        else:
            loop = QEventLoop()
            timer = QTimer()
            timer.setSingleShot(True)
            # reply or timeout break event loop, whoever comes first
            timer.timeout.connect(loop.quit)
            reply = self.manager.get(request)
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

        request = QNetworkRequest(qurl)

        def progress(b, total):
            if total > 0:
                self.progress.emit(int(100*b/total))

        self.reply = self.manager.get(request)
        self.reply.error.connect(
            lambda: self.error.emit(self.reply.errorString()))
        self.reply.downloadProgress.connect(progress)
        self.reply.finished.connect(
            lambda: self.finished.emit(Reply(self.reply)))
        #self.reply.readyRead.connect(ready_read)
        return 0

