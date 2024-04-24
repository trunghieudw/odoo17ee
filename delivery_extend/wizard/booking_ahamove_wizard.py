import requests
import logging
import json
from typing import Dict, Any
from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.addons.delivery_extend.dataclass.delivery_dataclasses import AhamoveDataclass
_logger = logging.getLogger(__name__)


class BookingAhamoveWizard(models.TransientModel):
    _name = 'booking.ahamove.wizard'

    @staticmethod
    def get_ahamove_service_types():
        return [
            ('SGN-BIKE', 'Sai Gon Bike'),
            ('SGN-EXPRESS', 'SG Đồ Ăn'),
            ('SGN-SAMEDAY', 'Ahamove 4H SGN'),
            ('HAN-BIKE', 'Ha Noi Bike'),
            ('VCA-BIKE', 'Can Tho Bike'),
            ('DAD-BIKE', 'Da Nang Bike'),
            ('SGN-VAN-1000', 'Sai Gon VAN1000'),
            ('HAN-VAN-1000', 'Ha Noi VAN1000')
        ]

    @staticmethod
    def get_payment_method():
        return [('online', 'Không thu tiền'), ('cod', 'Thu tiền khi giao hàng')]

    @staticmethod
    def get_payment():
        return [('CASH', 'CASH'), ('BALANCE', 'BALANCE')]

    @staticmethod
    def get_merchandises():
        return [
            ('TIER_1', 'Tiêu chuẩn'),
            ('TIER_2', 'Mức 1'),
            ('TIER_3', 'Mức 2'),
            ('TIER_4', 'Mức 3')
        ]

    deli_carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier', required=True, readonly=True)
    deli_order_id = fields.Many2one('stock.picking', string='Delivery order', required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    service_type = fields.Selection(
        selection=lambda self: BookingAhamoveWizard.get_ahamove_service_types(),
        string='Service Type', default='SGN-BIKE', required=True)
    payment_method = fields.Selection(selection=lambda self: BookingAhamoveWizard.get_payment_method(),
                                      string='Có thu tiền không?', default='online', required=True)
    payment = fields.Selection(selection=lambda self: BookingAhamoveWizard.get_payment(), string='Payment',
                               default='BALANCE', required=True)

    merchandises = fields.Selection(selection=lambda self: BookingAhamoveWizard.get_merchandises(),
                                    default='TIER_1', required=True)
    note = fields.Text(string='Note')
    cod = fields.Monetary(string='COD', currency_field='currency_id')
    no_of_package = fields.Integer(string='Number of package', default=1, required=True)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    sender_id = fields.Many2one('res.partner', string='Sender', required=True)
    sender_phone = fields.Char(string='Phone', required=True)
    sender_street = fields.Char(string='Street', required=True)
    sender_ward_id = fields.Many2one('res.ward', string='Ward')
    sender_district_id = fields.Many2one('res.district', string='District')
    sender_province_id = fields.Many2one('res.city', string='Province')

    is_back_to_pickup_point = fields.Boolean(string='Back to pick up point')

    receiver_id = fields.Many2one('res.partner', string='Receiver', required=True)
    receiver_phone = fields.Char(string='Phone', required=True)
    receiver_street = fields.Char(string='Street', required=True)
    receiver_ward_id = fields.Many2one('res.ward', string='Ward')
    receiver_district_id = fields.Many2one('res.district', string='District')
    receiver_province_id = fields.Many2one('res.city', string='Province')

    @api.onchange('receiver_province_id')
    def _onchange_receiver_province_id(self):
        for rec in self:
            if rec.receiver_province_id:
                return {
                    'domain':
                        {
                            'receiver_district_id': [('city_id', '=', rec.receiver_province_id.id)]
                        },
                }

    @api.onchange('receiver_district_id')
    def _onchange_receiver_district_id(self):
        for rec in self:
            if rec.receiver_district_id:
                return {
                    'domain':
                        {
                            'receiver_ward_id': [('district_id', '=', rec.receiver_district_id.id)]
                        },
                    }

    def _validate_ahamove_shipment(self):
        token = self.env.company.token_aha
        if not token:
            raise UserError(_('Please register to get tokens on ahamove!'))
        elif not self.service_type:
            raise UserError(_('The field service type is required.'))
        elif not self.payment_method:
            raise UserError(_('The field payment method is required.'))
        elif not self.warehouse_id:
            raise UserError(_("The field warehouse is required."))
        elif not self.sender_id:
            raise UserError(_("The field sender is required."))
        elif not self.sender_phone:
            raise UserError(_("The field sender phone is required."))
        elif not self.sender_street:
            raise UserError(_("The field sender street is required."))
        elif not self.receiver_id:
            raise UserError(_("The field receiver is required."))
        elif not self.receiver_phone:
            raise UserError(_("The field receiver phone is required."))
        elif not self.receiver_street:
            raise UserError(_("The field receiver street is required."))
        elif not self.payment:
            raise UserError(_("The field payment is required."))
        elif not self.merchandises:
            raise UserError(_("The field merchandises is required."))
        elif not self.no_of_package:
            raise UserError(_("The field number of package is required."))
        return token

    def _get_address_sender(self) -> str:
        street = self.sender_street or ''
        ward = self.sender_ward_id.name or ''
        district = self.sender_district_id.name or ''
        city = self.sender_province_id.name or ''
        country = self.sender_province_id.country_id.name or ''
        address = ', '.join([el for el in [street, ward, district, city, country] if el])
        return address

    def _get_address_receiver(self) -> str:
        street = self.receiver_street or ''
        ward = self.receiver_ward_id.name or ''
        district = self.receiver_district_id.name or ''
        city = self.receiver_province_id.name or ''
        country = self.receiver_province_id.country_id.name or ''
        address = ', '.join([el for el in [street, ward, district, city, country] if el])
        return address

    def _get_parameters_path(self) -> str:
        sender_address = self._get_address_sender()
        receiver_address = self._get_address_receiver()
        sender = '{'+f'"address":"{sender_address}","mobile":"{self.sender_phone}","name":"{self.sender_id.name}"'+'}'
        receiver = '{'+f'"address":"{receiver_address}","mobile":"{self.receiver_phone}","name":"{self.receiver_id.name}"'+'}'
        if self.deli_order_id.sale_id.payment_method == 'cod':
            receiver = receiver[:-1] + f',"cod":{int(self.cod)}' + receiver[-1:]
        path = '[{0},{1}]'.format(sender, receiver)
        return path

    def _get_payload_tr_ahamove(self, data: dict) -> Dict[str, Any]:
        payload: dict = {
            'name': data.get('order_id'),
            'tr_picking_id': self.deli_order_id.id,
            'tr_fee': data.get('order').get('total_pay'),
            'tr_total_fee': data.get('order').get('total_price'),
            'shared_link': data.get('shared_link'),
            'tr_address_sender': data.get('order').get('path')[0].get('address'),
            'tr_address_receiver': data.get('order').get('path')[1].get('address'),
        }
        if data.get('order').get('path')[1].get('cod'):
            payload.update({"tr_cod": data.get('order').get('path')[1].get('cod')})

        if data.get('status'):
            if data.get('status') == 'IN PROCESS':
                payload.update({"tr_status": "IN_PROCESS"})
            else:
                payload.update({"tr_status": data.get('status')})
        return payload

    def _get_payload_delivery_book(self, dataclass: AhamoveDataclass, data: dict) -> Dict[str, Any]:
        payload = {
            'carrier_id': self.deli_carrier_id.id,
            'service_type_aha': dataclass.service_id,
            'payment_method_aha': self.payment_method,
            'payment_aha': self.payment,
            'merchandises_aha': self.merchandises,
            'receiver_id': self.receiver_id.id,
            'receiver_phone': self.receiver_phone,
            'receiver_street': self.receiver_street,
            'receiver_ward_id': self.receiver_ward_id.id or False,
            'receiver_district_id': self.receiver_district_id.id or False,
            'receiver_province_id': self.receiver_province_id.id or False,
            'warehouse_id': self.warehouse_id.id,
            'sender_id': self.sender_id.id,
            'sender_phone': self.sender_phone,
            'sender_street': self.sender_street,
            'sender_ward_id': self.sender_ward_id.id or False,
            'sender_district_id': self.sender_district_id.id or False,
            'sender_province_id': self.sender_province_id.id or False,
            'deli_order_id': self.deli_order_id.id,
            'note': self.note,
            'num_of_package': self.no_of_package,
            'fee_ship': dataclass.total_price,
            'bl_code': dataclass.order_id,
            'cod': self.cod,
            'tracking_link': dataclass.shared_link,
            'state': dataclass.status,
            'json_create': json.dumps(data)
        }
        return payload

    def action_booking_ahamove(self):
        try:
            if self.deli_order_id.tr_ahamove_ids:
                if any(order.tr_status not in ['CANCELLED', 'FAILED', 'COMPLETED'] for order in self.deli_order_id.tr_ahamove_ids):
                    raise UserError(_("Can't create a new order because there's an order in progress!"))
            token = self._validate_ahamove_shipment()
            base_url = 'https://api.ahamove.com/v1/order/create'
            promo_code = self.env['ir.config_parameter'].sudo().get_param('tr_custom_field.promo_code')
            id_1 = ""
            id_2 = ""
            price = ['10000', '20000', '40000']
            if self.merchandises != 'TIER_1':
                service_request_1 = f'{self.service_type}-BULKY'
                if self.merchandises == 'TIER_2':
                    id_1 = '{' + f'"_id":"{service_request_1}","price":{price[0]},"tier_code":"{self.merchandises}"'+'}'
                elif self.merchandises == 'TIER_3':
                    id_1 = '{' + f'"_id":"{service_request_1}","price":{price[1]},"tier_code":"{self.merchandises}"'+'}'
                else:
                    id_1 = '{' + f'"_id":"{service_request_1}","price":{price[2]},"tier_code":"{self.merchandises}"'+'}'
            if self.is_back_to_pickup_point:
                service_request_2 = self.service_type + "-ROUND-TRIP"
                id_2 = '{' + f'"_id":"{service_request_2}"' + '}'

            if id_1 and id_2:
                rail = f'&service_id={self.service_type}&requests=[{id_1},{id_2}]&payment_method={self.payment}&promo_code={promo_code}'
            elif id_1:
                rail = f'&service_id={self.service_type}&requests=[{id_1}]&payment_method={self.payment}&promo_code={promo_code}'
            elif id_2:
                rail = f'&service_id={self.service_type}&requests=[{id_2}]&payment_method={self.payment}&promo_code={promo_code}'
            else:
                rail = f'&service_id={self.service_type}&requests=[]&payment_method={self.payment}&promo_code={promo_code}'

            path = self._get_parameters_path()
            url = f'{base_url}?token={token}&order_time=0&path={path}{rail}'
            if self.note:
                url += f'&remarks="{self.note}"'
            res = requests.post(url)
            _logger.info(f'[Ahamove] - Call API Create Order {url}')
            if res.status_code != 200:
                raise UserError(_(f'Order creation failed, please check again. {json.loads(res.content)}'))
            data = res.json()
            _logger.info(f'Response API Create Order Ahamove: {data}')
            payload_tr_ahamove = self._get_payload_tr_ahamove(data)
            dataclass = AhamoveDataclass(*AhamoveDataclass.load_data(data))
            payload_delivery_book = self._get_payload_delivery_book(dataclass, data)
            self.env['tr.ahamove'].sudo().create(payload_tr_ahamove)
            delivery_book_id = self.env['delivery.book'].sudo().create(payload_delivery_book)
            self.deli_order_id.write({'deli_book_id': delivery_book_id.id})
            self.deli_order_id.sale_id.write({'deli_book_id': delivery_book_id.id})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Delivery Book',
                'res_model': 'delivery.book',
                'view_mode': 'form',
                'res_id': delivery_book_id.id,
                'target': 'current',
            }
        except Exception as e:
            raise UserError(_(ustr(e)))
