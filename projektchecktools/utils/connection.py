from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QEventLoop, QTimer, QUrlQuery, QObject
from qgis.PyQt.QtCore import pyqtSignal
import json


class ConnectionError(Exception):
    pass


class Reply:
    def __init__(self, content='', status_code=200, url=''):
        self.status_code = status_code
        self.content = content
        self.url = url

    def raise_for_status(self):
        if self.status_code != 200:
            raise ConnectionError(self.status_code)

    def json(self):
        return json.loads(self.content)


class Request(QObject):
    finished = pyqtSignal(Reply)
    error = pyqtSignal(str)

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
        loop = QEventLoop()
        timer = QTimer()

        request = QNetworkRequest(qurl)
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
        content = reply.readAll().data()
        status_code = reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        reply.deleteLater()
        res = Reply(content=content, status_code=status_code,
                    url=reply.url().url())
        self.finished.emit(res)
        return res

    def _get_async(self, qurl: QUrl):
        request = QNetworkRequest(qurl)
        reply = self.manager.get(request)

        def finished(reply):
            content = reply.readAll().data()
            status_code = reply.attribute(
                QNetworkRequest.HttpStatusCodeAttribute)
            res = Reply(content=content, status_code=status_code,
                        url=reply.url().url())
            self.finished.emit(res)

        reply.error.connect(lambda r: self.error.emit(r.errorString()))
        reply.finished.connect(finished)
        return 0

