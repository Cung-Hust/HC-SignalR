import requests
from requests.exceptions import HTTPError
from requests.structures import CaseInsensitiveDict


class HttpRequest:
    __header: CaseInsensitiveDict
    __body: dict
    __url: str
    __cookie: dict

    @property
    def body(self):
        return self.__body

    @property
    def header(self):
        return self.__header

    @property
    def url(self):
        return self.__url

    @header.setter
    def header(self, header: CaseInsensitiveDict):
        self.__header = header

    @body.setter
    def body(self, body: dict):
        self.__body = body

    @url.setter
    def url(self, url: str):
        self.__url = url


class Http:
    def create_new_http_header(self, domitory_id: str = "", cookie: str = ""):
        new_http_header = CaseInsensitiveDict()
        new_http_header["Accept"] = "application/json"
        new_http_header["X-DormitoryId"] = domitory_id
        new_http_header["Cookie"] = cookie
        return new_http_header

    def create_new_http_request(
        self, url: str = None, body_data: dict = {}, header: CaseInsensitiveDict = {}
    ):
        new_http_request = HttpRequest()
        new_http_request.body = body_data
        new_http_request.header = header
        new_http_request.url = url
        return new_http_request

    def get(self, req: HttpRequest):
        resp = None
        try:
            resp = requests.get(req.url, headers=req.header)
            return resp
        except HTTPError as err:
            return ""
        except Exception as err:
            return ""

    def post(self, req: HttpRequest):
        try:
            resp = requests.post(req.url, headers=req.header, json=req.body)
            return resp
        except HTTPError as err:
            return ""
        except Exception as err:
            return ""

    def put(self, req: HttpRequest):
        resp = None
        try:
            resp = requests.put(req.url, headers=req.header, json=req.body)
            return resp
        except HTTPError as err:
            return ""
        except Exception as err:
            return ""

    async def delete(self, req: HttpRequest):
        resp = None
        try:
            resp = requests.delete(req.url, headers=req.header, json=req.body)
            return resp
        except HTTPError as err:
            return ""
        except Exception as err:
            return ""
