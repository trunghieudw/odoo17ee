import logging
import json
from odoo import _
from odoo.http import Controller, request, route  # pylint: disable=E0401
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

VIETTELPOST_STATUS_MAP = {
    '107': _('Canceled'),
    '201': _('Canceled'),
    '105': _('Has taken the goods'),
    '200': _('Being transported'),
    '202': _('Being transported'),
    '300': _('Being transported'),
    '320': _('Being transported'),
    '400': _('Being transported'),
    '507': _('On delivery'),
    '502': _('Approval to return'),
    '515': _('Approval to return'),
    '504': _('Successful return'),
    '505': _('Wait for approval to return'),
    '501': _('Successful delivery'),
}


class Main(Controller):
    @route("/viettelpost", type="json", auth="public")
    def handler(self):
        payload = request.jsonrequest
        data = payload.get('DATA', {})
        order_number = data.get('ORDER_NUMBER', '')
        order_status = str(data.get('ORDER_STATUS', ''))

        _logger.info('===============%s - %s', order_number, order_status)
        if order_number and (order_status in VIETTELPOST_STATUS_MAP.keys()):
            picking = request.env['stock.picking'].sudo().search([('carrier_tracking_ref', '=', order_number)])
            viettelpost_carrier_id = request.env['delivery.carrier'].sudo().search([('delivery_type', '=', 'viettelpost')])
            if not viettelpost_carrier_id:
                raise UserError(_('Delivery carrier Viettelpost not found.'))
            viettelpost_book_id = request.env['delivery.book'].sudo().search([
                ('bl_code', '=', data.get('_id')),
                ('carrier_id', '=', viettelpost_carrier_id.id)
            ])
            if not viettelpost_book_id:
                raise UserError(_('Delivery book ahamove not found.'))
            viettelpost_book_id.sudo().write({'state': data.get('status'), 'json_webhook': json.dumps(data)})
            _logger.info('===============%s', picking)
            if picking:
                for p in picking:
                    msg = VIETTELPOST_STATUS_MAP.get(order_status)
                    p.sale_id.write({'viettelpost_last_status': msg})
                    if order_status == '107':
                        p.carrier_tracking_ref = False
