from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore import QUrl, QEventLoop, QTimer, QUrlQuery
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


class Request:

    def __init__(self):
        pass

    def get(self, url, params=None, timeout=10000, verify=False):
        '''
        synchronous
        verify actually doesn't do anything, just to match requests api
        '''
        manager = QgsNetworkAccessManager.instance()
        loop = QEventLoop()
        timer = QTimer()
        qurl = QUrl(url)

        if params:
            query = QUrlQuery()
            for param, value in params.items():
                query.addQueryItem(param, str(value))
            qurl.setQuery(query.query())

        request = QNetworkRequest(qurl)
        timer.setSingleShot(True)
        # reply or timeout break event loop, whoever comes first
        timer.timeout.connect(loop.quit)
        reply = manager.get(request)
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
            raise ConnectionError(reply.errorString())
        content = reply.readAll().data()
        status_code = reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        reply.deleteLater()
        return Reply(content=content, status_code=status_code,
                     url=reply.url().url())

