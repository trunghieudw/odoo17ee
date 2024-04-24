import functools
import odoo
import json
import re
from datetime import datetime, date
from typing import Dict, Any

from odoo.http import Controller, request, route


STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_UNAUTHORIZED = 401
STATUS_NOT_FOUND = 404


def default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)


def valid_response(message: str, status: int = STATUS_OK):
    """Valid Response
    This will be return when the http request was successfully processed."""
    return {'status': 'success', 'message': message}


def invalid_response(message: str, status: int):
    """
        Invalid Response
        This will be the return value whenever the server runs into an error
        either from the client or the server.
    """
    return {'status': 'error', 'message': message}


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        path = request.httprequest.path
        if re.search(r"viettelpost", path):
            authorization = request.httprequest.headers.get('Authorization')
            if not authorization:
                return invalid_response('The header Authorization missing', STATUS_BAD_REQUEST)
            partner_code = 'VTP'
        elif re.search(r"ahamove", path):
            authorization = request.httprequest.headers.get('apikey')
            if not authorization:
                return invalid_response('The header apikey missing', STATUS_BAD_REQUEST)
            partner_code = 'AHAMOVE'
        else:
            return invalid_response('Path is not formatted', STATUS_BAD_REQUEST)
        token = request.env['res.partner'].sudo().search([('partner_code', '=', partner_code),
                                                         ('authorization', "=", authorization)], limit=1)
        if not token:
            return invalid_response('The token seems to have invalid.', STATUS_NOT_FOUND)
        return func(self, *args, **kwargs)
    return wrap


class WebhookDeliController(Controller):

    @staticmethod
    def _validate_payload_webhook_viettelpost(payload: Dict[str, Any]):
        if not payload:
            return invalid_response(f'The payload is required.', STATUS_BAD_REQUEST)
        elif 'ORDER_NUMBER' not in payload:
            return invalid_response(f'The field ORDER_NUMBER missing.', STATUS_BAD_REQUEST)
        elif 'STATUS_NAME' not in payload:
            return invalid_response(f'The field STATUS_NAME missing.', STATUS_BAD_REQUEST)
        elif not payload.get('ORDER_NUMBER'):
            return invalid_response(f'The value of field ORDER_NUMBER is empty.', STATUS_BAD_REQUEST)
        elif not payload.get('STATUS_NAME'):
            return invalid_response(f'The value of field STATUS_NAME is empty.', STATUS_BAD_REQUEST)
        else:
            return True

    @staticmethod
    def _validate_payload_webhook_ahamove(payload: Dict[str, Any]):
        if not payload:
            return invalid_response(f'The payload is required.', STATUS_BAD_REQUEST)
        elif '_id' not in payload:
            return invalid_response(f'The field _id missing.', STATUS_BAD_REQUEST)
        elif 'status' not in payload:
            return invalid_response(f'The field status missing.', STATUS_BAD_REQUEST)
        elif not payload.get('_id'):
            return invalid_response(f'The value of field _id is empty.', STATUS_BAD_REQUEST)
        elif not payload.get('status'):
            return invalid_response(f'The value of field status is empty.', STATUS_BAD_REQUEST)
        else:
            return True

    @validate_token
    @route('/api/v1/webhook/viettelpost', type='json', auth='none', methods=["POST"], csrf=False)
    def _update_delivery_book_viettelpost(self):
        try:
            db = request.session.db
            registry = odoo.modules.registry.Registry(db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                payload = request.jsonrequest.get('DATA')
                is_valid = WebhookDeliController._validate_payload_webhook_viettelpost(payload)
                if is_valid is not True:
                    return is_valid
                delivery_book_id = env['delivery.book'].search([('bl_code', '=', payload.get('ORDER_NUMBER'))], limit=1)
                if not delivery_book_id:
                    return invalid_response(f'The order number {payload.get("ORDER_NUMBER")} not found.', STATUS_NOT_FOUND)
                delivery_book_id.write({
                    'state': payload.get('STATUS_NAME', ''),
                    'json_webhook': json.dumps(payload),
                    'weight': payload.get('PRODUCT_WEIGHT', 0),
                    'money_total': payload.get('MONEY_TOTAL', 0),
                    'money_collection_fee': payload.get('MONEY_COLLECTION', 0),
                    'note': payload.get('NOTE', ''),
                })
                return valid_response('The odoo received data successfully.')
        except Exception as error:
            return invalid_response(f'[Webhook Viettelpost] - Exception: {error}', STATUS_NOT_FOUND)

    @validate_token
    @route('/api/v1/webhook/ahamove', type='json', auth='none', methods=["POST"], csrf=False)
    def _update_delivery_book_ahamove(self):
        try:
            db = request.session.db
            registry = odoo.modules.registry.Registry(db)
            with odoo.api.Environment.manage(), registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                payload = request.jsonrequest
                is_valid = WebhookDeliController._validate_payload_webhook_ahamove(payload)
                if is_valid is not True:
                    return is_valid
                delivery_book_id = env['delivery.book'].sudo().search([('bl_code', '=', payload.get('_id'))], limit=1)
                if not delivery_book_id:
                    return invalid_response(f'The order number {payload.get("_id")} not found.', STATUS_NOT_FOUND)
                delivery_book_id.write({'state': payload.get('status'), 'json_webhook': json.dumps(payload)})
                return valid_response('The odoo received data successfully.')
        except Exception as error:
            return invalid_response(f'[Webhook Ahamove] - Exception: {error}', STATUS_NOT_FOUND)
