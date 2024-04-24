import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from odoo import models, fields, _, api
from odoo.tools import ustr
from odoo.exceptions import ValidationError, UserError
from odoo.addons.delivery_extend.dataclass.delivery_dataclasses import ViettelpostDataclass
from odoo.addons.delivery_extend.api.client import Client

_logger = logging.getLogger(__name__)


class BookingViettelpostWizard(models.TransientModel):
    _name = 'booking.viettelpost.wizard'
    _description = 'This module fills and confirms info about shipment before creating a bill of lading Viettelpost.'

    @staticmethod
    def get_viettelpost_service_types() -> List[Tuple]:
        return [
            ('VCN', 'Tài liệu nhanh'),
            ('NCOD', 'Chuyển phát nhanh'),
            ('LCOD', 'Chuyển phát tiêu chuẩn'),
            # ('V24', 'Đồng giá 24K'),
            # ('LECO', 'Hàng nặng tiết kiệm'),
            # ('VTK', 'Tài liệu tiết kiệm'),
            # ('V60', 'V60 Dịch vụ Nhanh 60h'),
            # ('VHT', 'Hỏa tốc, hẹn giờ'),
            # ('SCOD', 'SCOD Giao hàng thu tiền'),
            # ('PTN', 'Nội tỉnh nhanh'),
            # ('V25', 'V25'),
            # ('V30', 'V30'),
            # ('V20', 'V20'),
            # ('PHS', 'Nội tỉnh tiết kiệm'),
            # ('V35', 'V35'),
            # ('VBS', 'VBS Nhanh theo hộp'),
            # ('V02', 'TMDT Phát nhanh 2h'),
            # ('VBE', 'VBE Tiết kiệm theo hộp'),
            # ('ECOD', 'ECOD Giao hành thu tiền tiết kiệm'),
            # ('LSTD', 'Hàng nặng nhanh'),
            # ('VCBA', 'Chuyển phát đường bay'),
            # ('VCBO', 'Chuyển phát đường bộ'),
            # ('V505', 'Dịch vụ 5+ gói 500g'),
            # ('V510', 'Dịch vụ 5+ gói 1000g'),
            # ('V520', 'Dịch vụ 5+ gói 2000g'),
            # ('PTTT', 'Phân tích thị trường'),
            # ('DHC', 'DHL Chuyển phát quốc tế'),
            # ('UPS', 'UPS quốc tế chỉ định'),
            # ('VQN', 'VQN Quốc tế nhanh'),
            # ('VQE', 'VQE Quốc tế chuyên tuyến'),
            # ('VVC', 'VVC Giao voucher thu tiền'),
            # ('VCT', 'VCT Chuyển tiền nhận tại địa chỉ'),
        ]

    @staticmethod
    def viettelpost_order_payments() -> List[Tuple]:
        return [('1', _('Uncollect money')),
                ('2', _('Collect express fee and price of goods.')),
                ('3', _('Collect price of goods')),
                ('4', _('Collect express fee'))]

    @staticmethod
    def viettelpost_product_types() -> List[Tuple]:
        return [('TH', 'Envelope'), ('HH', 'Goods')]

    @staticmethod
    def viettelpost_national_types() -> List[Tuple]:
        return [('1', 'Inland'), ('0', 'International')]

    deli_carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier', required=True, readonly=True)
    service_type = fields.Selection(
        selection=lambda self: BookingViettelpostWizard.get_viettelpost_service_types(),
        string='Service Type', default='VCN', required=True)
    order_payment = fields.Selection(selection=lambda self: BookingViettelpostWizard.viettelpost_order_payments(),
                                     string='Order Payment', default='1', required=True)
    product_type = fields.Selection(selection=lambda self: BookingViettelpostWizard.viettelpost_product_types(),
                                    string='Product Type', default='HH', required=True)
    national_type = fields.Selection(selection=lambda self: BookingViettelpostWizard.viettelpost_national_types(),
                                     string='National Type', default='1', required=True)
    receiver_id = fields.Many2one('res.partner', string='Receiver', required=True)
    receiver_phone = fields.Char(string='Phone', required=True)
    receiver_street = fields.Char(string='Street', required=True)
    receiver_ward_id = fields.Many2one('res.ward', string='Ward', required=True)
    receiver_district_id = fields.Many2one('res.district', string='District', required=True)
    receiver_province_id = fields.Many2one('res.city', string='Province', required=True)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    sender_id = fields.Many2one('res.partner', string='Sender', required=True)
    sender_phone = fields.Char(string='Phone', required=True)
    sender_street = fields.Char(string='Address', required=True)
    sender_ward_id = fields.Many2one('res.ward', string='Ward', required=True)
    sender_district_id = fields.Many2one('res.district', string='District', required=True)
    sender_province_id = fields.Many2one('res.city', string='Province', required=True)

    store_id = fields.Many2one('viettelpost.store', string='Store', required=True)
    deli_order_id = fields.Many2one('stock.picking', string='Delivery order', required=True, readonly=True)
    check_unique = fields.Boolean(string='Check unique', help='Check unique to check SO exists in Viettelpost.')
    note = fields.Text(string='Note')
    product_name = fields.Char(string='Product name', required=True)
    no_of_package = fields.Integer(string='Number of package', required=True, default=1)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    cod = fields.Monetary(string='COD', currency_field='currency_id')
    weight = fields.Float(string='Weight')

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

    def _get_address_sender(self) -> str:
        street = self.sender_street or ''
        ward = self.sender_ward_id.name or ''
        district = self.sender_district_id.name or ''
        city = self.sender_province_id.name or ''
        country = self.sender_province_id.country_id.name or ''
        address = ', '.join([el for el in [street, ward, district, city, country] if el])
        return address

    def _get_sender(self) -> Dict[str, Any]:
        sender: dict = {
            'SENDER_FULLNAME': self.sender_id.name,
            'SENDER_ADDRESS': self._get_address_sender(),
            'SENDER_PHONE': self.sender_id.phone,
            'SENDER_EMAIL': self.sender_id.email or '',
            'SENDER_WARD': self.sender_id.ward_id.viettelpost_wards_id,
            'SENDER_DISTRICT': self.sender_id.district_id.viettelpost_district_id,
            'SENDER_PROVINCE': self.sender_id.city_id.viettelpost_province_id,
            'SENDER_LATITUDE': 0,
            'SENDER_LONGITUDE': 0,
        }
        return sender

    def _get_address_receiver(self) -> str:
        street = self.receiver_street or ''
        ward = self.receiver_ward_id.name or ''
        district = self.receiver_district_id.name or ''
        city = self.receiver_province_id.name or ''
        country = self.receiver_province_id.country_id.name or ''
        address = ', '.join([el for el in [street, ward, district, city, country] if el])
        return address

    def _get_receiver(self) -> Dict[str, Any]:
        receiver = {
            'RECEIVER_FULLNAME': self.receiver_id.name,
            'RECEIVER_ADDRESS': self._get_address_receiver(),
            'RECEIVER_PHONE': self.receiver_phone,
            'RECEIVER_EMAIL': self.receiver_id.email or '',
            'RECEIVER_WARD': self.receiver_ward_id.viettelpost_wards_id,
            'RECEIVER_DISTRICT': self.receiver_district_id.viettelpost_district_id,
            'RECEIVER_PROVINCE': self.receiver_province_id.viettelpost_province_id,
            'RECEIVER_LATITUDE': 0,
            'RECEIVER_LONGITUDE': 0,
        }
        return receiver

    def _get_list_item(self) -> Dict[str, List[Dict[str, Any]]]:
        lst_item: dict = {
            'LIST_ITEM': [
                {
                    'PRODUCT_NAME': line.product_id.product_tmpl_id.name,
                    'PRODUCT_PRICE': line.price_subtotal,
                    'PRODUCT_WEIGHT': line.product_id.product_tmpl_id.weight,
                    'PRODUCT_QUANTITY': line.product_uom_qty
                } for line in self.deli_order_id.sale_id.order_line if not line.is_delivery
            ]
        }
        return lst_item

    def _validate_payload(self):
        fields = {
            'Delivery carrier': self.deli_carrier_id,
            'Delivery order': self.deli_order_id,
            'Sender': self.sender_id,
            'Sender Phone': self.sender_phone,
            'Sender Street': self.sender_street,
            'Sender Ward': self.sender_ward_id,
            'Sender District': self.sender_district_id,
            'Sender Province': self.sender_province_id,
            'Store': self.store_id,
            'Service Type': self.service_type,
            'Order Payment': self.order_payment,
            'Product Type': self.product_type,
            'National Type': self.national_type,
            'Product Name': self.product_name,
            'Number of Package': self.no_of_package,
            'Receiver': self.receiver_id,
            'Receiver Phone': self.receiver_phone,
            'Receiver Street': self.receiver_street,
            'Receiver Ward': self.receiver_ward_id,
            'Receiver District': self.receiver_district_id,
            'Receiver Province': self.receiver_province_id,
            'List Item': len(self.deli_order_id.sale_id.order_line)
        }
        for field, value in fields.items():
            if not value:
                raise ValidationError(_(f'The field {field} is required.'))

    def _get_delivery_book_payload(self, dataclass: ViettelpostDataclass) -> Dict[str, Any]:
        payload = {
            'carrier_id': self.deli_carrier_id.id,
            'service_type': self.service_type,
            'order_payment': self.order_payment,
            'product_type': self.product_type,
            'national_type': self.national_type,
            'receiver_id': self.receiver_id.id,
            'receiver_phone': self.receiver_phone,
            'receiver_street': self.receiver_street,
            'receiver_ward_id': self.receiver_ward_id.id,
            'receiver_district_id': self.receiver_district_id.id,
            'receiver_province_id': self.receiver_province_id.id,
            'store_id': self.store_id.id,
            'warehouse_id': self.warehouse_id.id,
            'sender_id': self.sender_id.id,
            'sender_phone': self.sender_phone,
            'sender_street': self.sender_street,
            'sender_ward_id': self.sender_ward_id.id,
            'sender_district_id': self.sender_district_id.id,
            'sender_province_id': self.sender_province_id.id,
            'deli_order_id': self.deli_order_id.id,
            'note': self.note or '',
            'num_of_package': self.no_of_package,
            'fee_ship': dataclass.money_total_fee,
            'money_total': dataclass.money_total,
            'money_fee': dataclass.money_fee,
            'money_collection_fee': dataclass.money_collection_fee,
            'money_vat': dataclass.money_vat,
            'money_other_fee': dataclass.money_other_fee,
            'bl_code': dataclass.bl_code,
            'cod': dataclass.money_collection,
            'weight': dataclass.exchange_weight,
            'est_deli_time': dataclass.kpi_ht,
            'tracking_link': f'https://viettelpost.vn/thong-tin-don-hang?peopleTracking=sender&orderNumber={dataclass.bl_code}',
            'state': 'Giao cho buu ta di nhan',
        }
        return payload

    def _get_client_viettelpost(self) -> Client:
        base_url = 'https://partner.viettelpost.vn'
        if not base_url:
            raise UserError(_('Web base url not found.'))
        if not self.deli_carrier_id.viettelpost_token:
            raise UserError(_('Viettelpost token not found.'))
        client = Client(base_url, self.deli_carrier_id.viettelpost_token)
        return client

    def _prepare_data_update_carrier_to_stock_picking(self, payload: dict, dataclass_vtp: ViettelpostDataclass) -> Dict[str, Any]:
        payload: dict = {
            'carrier_id': self.deli_carrier_id.id,
            'viettelpost_store_id': self.store_id.id,
            'viettelpost_default_service_type': self.service_type,
            'viettelpost_product_type': self.product_type,
            'viettelpost_national_type': self.national_type,
            'viettelpost_order_payment': self.order_payment,
            'carrier_tracking_url': payload.get('tracking_link'),
            'carrier_tracking_ref': dataclass_vtp.bl_code,
            'shipping_weight': dataclass_vtp.exchange_weight
        }
        return payload

    def _prepare_data_create_line_amount_ship_fee(self, dataclass: ViettelpostDataclass):
        service_name = [item[1] for item in BookingViettelpostWizard.get_viettelpost_service_types() if item[0] == self.service_type]
        payload: dict = {
            'product_id': self.deli_carrier_id.product_id.id,
            'name': f'[{self.service_type}] - {service_name[0]}',
            'product_uom_qty': 1.0,
            'price_unit': dataclass.money_total,
            'price_subtotal': dataclass.money_total,
            'price_total': dataclass.money_total,
            'sequence': self.deli_order_id.sale_id.order_line[-1].sequence + 1,
            'order_id': self.deli_order_id.sale_id.order_line[-1].order_id.id,
            'is_delivery': True
        }
        return payload

    def action_booking_viettelpost(self):
        try:
            self._validate_payload()
            payload = {
                'ORDER_NUMBER': self.deli_order_id.name,
                'GROUPADDRESS_ID': self.store_id.group_address_id,
                'CUS_ID': self.store_id.customer_id,
                'DELIVERY_DATE': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'PRODUCT_NAME': self.product_name,
                'PRODUCT_QUANTITY': self.no_of_package,
                'PRODUCT_PRICE': self.deli_order_id.sale_id.amount_total,
                'PRODUCT_WEIGHT': self.weight,
                'ORDER_NOTE': self.note or '',
                'MONEY_COLLECTION': self.cod,
                'PRODUCT_TYPE': self.product_type,
                'ORDER_PAYMENT': int(self.order_payment),
                'ORDER_SERVICE': self.service_type
            }
            sender = self._get_sender()
            receiver = self._get_receiver()
            lst_item = self._get_list_item()
            payload = {**payload, **sender, **receiver, **lst_item}
            if self.check_unique:
                payload = {**payload, **{'CHECK_UNIQUE': True}}
            _logger.info(f'[Viettelpost] - Payload: {payload}')
            client = self._get_client_viettelpost()
            result = client.create_order(payload)
            dataclass_vtp = ViettelpostDataclass(*ViettelpostDataclass.load_data(result))
            delivery_book_payload = self._get_delivery_book_payload(dataclass_vtp)
            delivery_book_id = self.env['delivery.book'].sudo().create(delivery_book_payload)
            stock_picking_payload = self._prepare_data_update_carrier_to_stock_picking(payload, dataclass_vtp)
            stock_picking_payload = {**stock_picking_payload, **{'deli_book_id': delivery_book_id.id}}
            self.deli_order_id.write(stock_picking_payload)
            self.deli_order_id.sale_id.write({'deli_book_id': delivery_book_id.id})
            # self._create_or_update_order_line_type_delivery(delivery_book_id, dataclass_vtp)
            delivery_book_id.write({'json_create': json.dumps(delivery_book_payload)})
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
