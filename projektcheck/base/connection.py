import requests


class ConnectionError(Exception):
    pass


class Request:
    def __init__(self):
        pass

    def get(self, url, params=None, verify=None):
        try:
            r = requests.get(url, params=params,
                             verify=False)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(str(e))
        return r.text
