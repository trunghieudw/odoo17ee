import logging
from typing import Dict

import requests

_logger = logging.getLogger(__name__)


class ViettelPostRequest:
    def __init__(self, token: str, prod_environment: bool):
        self.endurl = "https://partner.viettelpost.vn/v2/"
        if not prod_environment:
            self.endurl = "https://partner.viettelpost.vn/v2/"

        # Basic detail require to authenticate
        self.token = token

    def _add_security_header(self, client: 'requests.Session') -> None:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers['token'] = self.token
        client.headers.update(headers)

    def _set_client(self) -> 'requests.Session':
        session = requests.Session()
        self._add_security_header(session)
        return session

    def _get_response_message(self, response: 'requests.Response') -> Dict:
        error_message = False
        data = {}
        if response.ok:
            data = response.json()
            if data.get("error"):
                error_message = data.get("message")
            else:
                data = data["data"]

        return {"error_message": error_message, "data": data}

    def _request(self, client: 'requests.Session', url: str, **kwargs):
        try:
            response = client.request(url=url, **kwargs)
            data = self._get_response_message(response)
        except Exception:
            data = {"error_message": "HTTP Exception"}

        return data

    def get_districts(self, province_id: int):
        params = {"provinceId": province_id}
        client = self._set_client()
        self._add_security_header(client)
        response = self._request(client, self.endurl + 'categories/listDistrict', method='get', params=params)
        return response

    def get_wards(self, district_id: int):
        params = {"districtId": district_id}
        client = self._set_client()
        self._add_security_header(client)
        response = self._request(client, self.endurl + 'categories/listWards', method='get', params=params)
        return response
