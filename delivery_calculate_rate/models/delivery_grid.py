import json
import logging
import requests
from typing import Dict, Any, Optional
from odoo import models, fields, _
from odoo.tools import ustr
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, AccessDenied, AccessError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('google_map', 'Google Map'),
        ('ahamove', 'Ahamove')
    ], ondelete={'google_map': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0}),
                 'ahamove': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    @staticmethod
    def builder_result_rate_shipment(price: float,
                                     success: Optional[bool] = True,
                                     error_msg: Optional[str] = False,
                                     warning_msg: Optional[str] = False) -> Dict[str, Any]:
        return {'success': success, 'price': price, 'error_message': error_msg, 'warning_message': warning_msg}

    def _check_address(self, address):
        self.ensure_one()
        fields_check = {'contact_address': 'contact_address', 'phone': 'phone'}
        rec = [fields_check[field] for field in fields_check if not address[field]]
        if rec:
            raise UserError(_(f'The fields {rec} is required'))

    def _calculate_distance(self, order):
        token = self.env['ir.config_parameter'].sudo().get_param('google_map_token')
        url = self.env['ir.config_parameter'].sudo().get_param('google_map_api_cal_distance')
        if not token or not url:
            raise UserError(_('The system parameters token or url google map does not exists.'))
        origin = order.warehouse_id.partner_id
        self._check_address(origin)
        destination = order.partner_shipping_id
        self._check_address(destination)
        url = url.format(origin=origin.contact_address, destination=destination.contact_address, token=token).replace('\n', ',')
        try:
            response = requests.get(url)
            data = json.loads(response.content)
            _logger.info(f'[Google Map] - API Calculate Distance\n{url}')
            if response.status_code != 200:
                _logger.error(f'[Google Map] - API Calculate Distance Error.')
                raise AccessError(_(f'Request Google Map API Calculate Distance Error.'))
            if data['status'] == 'OK':
                distance = data['routes'][0]['legs'][0]['distance']['value'] / 1000
                return distance
            else:
                _logger.error(f'[Google Map] - API Calculate Distance Error. {data.get("error_message")}')
                raise AccessError(_(f'Request Google Map API Calculate Distance Error.'))
        except Exception as e:
            _logger.exception(f'[Google Map] - API Calculate Distance Error. {ustr(e)}')
            raise UserError(_(f'Call Google Map API Calculate Distance Exception. {ustr(e)}'))

    def _get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        total = weight = volume = quantity = distance = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = (order.amount_total or 0.0) - total_delivery
        total = order.currency_id._convert(
            total, order.company_id.currency_id, order.company_id, order.date_order or fields.Date.today())
        if self.delivery_type == 'google_map':
            distance = self._calculate_distance(order)
        return self._get_price_from_picking(total, weight, volume, quantity, distance)

    def _get_price_from_picking(self, total, weight, volume, quantity, distance):
        price = 0.0
        criteria_found = False
        price_dict = {
            'price': total,
            'volume': volume,
            'weight': weight,
            'wv': volume * weight,
            'quantity': quantity,
            'km': distance
        }
        if self.free_over and total >= self.amount:
            return 0
        for line in self.price_rule_ids:
            test = safe_eval(line.variable + line.operator + str(line.max_value), price_dict)
            if test:
                price = line.list_base_price + line.list_price * price_dict[line.variable_factor]
                criteria_found = True
                break
        if not criteria_found:
            raise UserError(_("No price rule matching this order; delivery cost cannot be computed."))
        return price

    def google_map_rate_shipment(self, order):
        return self.base_on_rule_rate_shipment(order)

    def ahamove_rate_shipment(self, order):
        url = self.env['ir.config_parameter'].sudo().get_param('ahamove_api_est_fee')
        if not url:
            raise UserError(_('The url estimate fee not found.'))
        token = self.env.company.token_aha
        if not token:
            raise UserError(_(f'The token of company {self.env.company.name} not found.'))
        ahamove_service = self.env.context.get('ahamove_service')
        url = url.format(token=token)
        rail = f'&service_id={ahamove_service}&requests=[]'
        sender_id = order.warehouse_id.partner_id
        self._check_address(sender_id)
        recipient_id = order.partner_shipping_id
        self._check_address(recipient_id)
        sender_address = '{' + f'"address": "{sender_id.contact_address}","mobile": "{sender_id.phone}"' + '}'
        recipient_address = '{' + f'"address": "{recipient_id.contact_address}","mobile": "{recipient_id.phone}"' + '}'
        url = f'{url}&order_time=0&path=[{sender_address},{recipient_address}]{rail}'.replace('\n', ',')
        try:
            response = requests.post(url)
            _logger.info(f'[Ahamove] - API Estimate Fee\n{url}')
            data = response.json()
            if response.status_code != 200:
                _logger.error(f'[Ahamove] - API Estimate Fee Error. {data["title"]} - {data["description"]}')
                return self.builder_result_rate_shipment(0.0, False, f'{data["title"]} - {data["description"]}')
            _logger.info(f'[Ahamove] - API Estimate Fee Successfully. Estimate Fee: {data["total_price"]}')
            return self.builder_result_rate_shipment(data['total_price'])
        except Exception as e:
            _logger.exception(f'[Ahamove] - API Estimate Fee Error. {ustr(e)}')
            return self.builder_result_rate_shipment(0.0, False, ustr(e))


class PriceRule(models.Model):
    _inherit = 'delivery.price.rule'

    variable = fields.Selection(selection_add=[('km', 'Km')], ondelete={'km': 'set default'})
    variable_factor = fields.Selection(selection_add=[('km', 'Km')], ondelete={'km': 'set default'})

