import json
import logging
from odoo import http, _, SUPERUSER_ID
from odoo.http import request
from odoo.tools import ustr

_logger = logging.getLogger(__name__)


class OnboardingController(http.Controller):

    @http.route('/partner/update_ahamove_status', type='json', auth='public', methods=['POST'], csrf=False)
    def update_ahamove_status(self, **kwargs):
        """ Returns status Ahamove """
        data = json.loads(request.httprequest.data)
        _logger.info(f'[Webhook Ahamove] - Start receive data: {data}')
        if not data:
            return {'success': False, 'error': 'Missing body from webhook'}
        AhamoveModel = request.env['tr.ahamove'].with_user(SUPERUSER_ID).sudo()
        DeliveryBookModel = request.env['delivery.book'].with_user(SUPERUSER_ID).sudo()
        try:
            ahamove = AhamoveModel.search([('name', '=', data.get('_id'))])
            book_id = DeliveryBookModel.search([('bl_code', '=', data.get('_id'))])
            if not book_id:
                return {'success': False, 'message': f'_id: {data.get("_id")} not found'}
            book_id.with_user(SUPERUSER_ID).sudo().write({'state': data.get('status'), 'json_webhook': json.dumps(data)})
            if ahamove and data.get('status') != "IN PROCESS":
                ahamove.write({
                    'tr_status': data.get('status'),
                    'tr_supplier_id': data.get('supplier_id'),
                    'tr_supplier_name': data.get('supplier_name'),
                })
            elif ahamove and data.get('status') == "IN PROCESS":
                ahamove.write({
                    'tr_status': "IN_PROCESS",
                    'tr_supplier_id': data.get('supplier_id'),
                    'tr_supplier_name': data.get('supplier_name'),
                })
            return {'success': True, 'message': 'Received successfully.'}
        except Exception as e:
            return {'success': False, 'error': f'{ustr(e)}'}

