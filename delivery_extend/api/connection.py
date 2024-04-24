import requests
import logging
from odoo.exceptions import UserError
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)

API_ROUTES = {
    'CreateOrder': '/v2/order/createOrder'
}


class Connection:
    def __init__(self, host, token):
        self.host = host
        self.token = token

    def execute_restful(self, func_name, method, *args, **kwargs):
        try:
            if func_name not in API_ROUTES:
                raise UserError(_('The API %s is not exist.') % func_name)
            endpoint = API_ROUTES[func_name]
            url = f'{self.host}{endpoint}'
            headers = {
                'Content-Type': 'application/json',
                'Token': self.token,
            }
            if method == 'GET':
                res = requests.get(url, params=kwargs, headers=headers, timeout=300)
            elif method == 'POST':
                res = requests.post(url, json=kwargs, headers=headers, timeout=300)
            elif method == 'DELETE':
                res = requests.delete(url, json=kwargs, headers=headers, timeout=300)
            else:
                res = requests.put(url, json=kwargs, headers=headers, timeout=300)
            try:
                data = res.json()
            except Exception as ex:
                raise ex
            if res.status_code != 200:
                raise UserError(_('Request failed with status: %s - Message: %s') % (res.status_code, data['message']))
            return data
        except Exception as e:
            raise e