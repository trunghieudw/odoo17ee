# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError
from odoo.tools.translate import _


from .connection import Connection

_logger = logging.getLogger(__name__)


class Client:

    def __init__(self, host, access_token):
        self.conn = Connection(host, access_token)

    def create_order(self, data):
        res = self.conn.execute_restful('CreateOrder', 'POST', **data)
        res = Client.check_response(res)
        return res

    @staticmethod
    def check_response(res):
        if res['status'] == 200:
            res = res['data']
        else:
            raise UserError(_(f'Request API failed. {res.get("message", "")}'))
        return res
