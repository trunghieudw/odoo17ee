from odoo import _, fields, models
from odoo.exceptions import UserError

from .viettelpost_request import ViettelPostRequest


class ProviderViettelPost(models.Model):
    _inherit = 'delivery.carrier'

    def _get_viettelpost_service_types(self):
        return [
            ('VCN', 'Tài liệu nhanh'),
            ('V24', 'Đồng giá 24K'),
            ('LECO', 'Hàng nặng tiết kiệm'),
            ('VTK', 'Tài liệu tiết kiệm'),
            ('V60', 'V60 Dịch vụ Nhanh 60h'),
            ('VHT', 'Hỏa tốc, hẹn giờ'),
            ('NCOD', 'Chuyển phát nhanh'),
            ('SCOD', 'SCOD Giao hàng thu tiền'),
            ('PTN', 'Nội tỉnh nhanh'),
            ('V25', 'V25'),
            ('V30', 'V30'),
            ('V20', 'V20'),
            ('PHS', 'Nội tỉnh tiết kiệm'),
            ('V35', 'V35'),
            ('VBS', 'VBS Nhanh theo hộp'),
            ('V02', 'TMDT Phát nhanh 2h'),
            ('VBE', 'VBE Tiết kiệm theo hộp'),
            ('LCOD', 'Chuyển phát tiêu chuẩn'),
            ('ECOD', 'ECOD Giao hành thu tiền tiết kiệm'),
            ('LSTD', 'Hàng nặng nhanh'),
            ('VCBA', 'Chuyển phát đường bay'),
            ('VCBO', 'Chuyển phát đường bộ'),
            ('V505', 'Dịch vụ 5+ gói 500g'),
            ('V510', 'Dịch vụ 5+ gói 1000g'),
            ('V520', 'Dịch vụ 5+ gói 2000g'),
            ('PTTT', 'Phân tích thị trường'),
            ('V510', 'Dịch vụ 5+ gói 1000g'),
            ('V02', 'TMDT Phát nhanh 2h'),
            ('V520', 'Dịch vụ 5+ gói 2000g'),
            ('VCBO', 'Chuyển phát đường bộ'),
            ('VCBA', 'Chuyển phát đường bay'),
            ('LSTD', 'Hàng nặng nhanh'),
            ('V505', 'Dịch vụ 5+ gói 500g'),
            ('PTTT', 'Phân tích thị trường'),
            ('NCOD', 'Chuyển phát nhanh'),
            ('SCOD', 'SCOD Giao hàng thu tiền'),
            ('PTN', 'Nội tỉnh nhanh'),
            ('V30', 'V30'),
            ('V25', 'V25'),
            ('PHS', 'Nội tỉnh tiết kiệm'),
            ('V20', 'V20'),
            ('V35', 'V35'),
            ('VCN', 'Tài liệu nhanh'),
            ('V24', 'Đồng giá 24K'),
            ('LECO', 'Hàng nặng tiết kiệm'),
            ('VTK', 'Tài liệu tiết kiệm'),
            ('V60', 'V60 Dịch vụ Nhanh 60h'),
            ('VHT', 'Hỏa tốc, hẹn giờ'),
            ('VBS', 'VBS Nhanh theo hộp'),
            ('VBE', 'VBE Tiết kiệm theo hộp'),
            ('LCOD', 'Chuyển phát tiêu chuẩn'),
            ('ECOD', 'ECOD Giao hành thu tiền tiết kiệm'),
            ('DHC', 'DHL Chuyển phát quốc tế'),
            ('UPS', 'UPS quốc tế chỉ định'),
            ('VQN', 'VQN Quốc tế nhanh'),
            ('VQE', 'VQE Quốc tế chuyên tuyến'),
            ('VVC', 'VVC Giao voucher thu tiền'),
            ('VCT', 'VCT Chuyển tiền nhận tại địa chỉ'),
        ]

    def _viettelpost_order_payments(self):
        return [('1', _('Uncollect money')), ('2', _('Collect express fee and price of goods.')), ('3', _('Collect price of goods')), ('4', _('Collect express fee'))]

    def _viettelpost_product_types(self):
        return [('TH', 'Envelope'), ('HH', 'Goods')]

    def _viettelpost_national_types(self):
        return [('1', 'Inland'), ('0', 'International')]

    delivery_type = fields.Selection(selection_add=[('viettelpost', 'Viettel Post')], ondelete={'viettelpost': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref('base.VND'), readonly=True)
    viettelpost_token = fields.Char(string='Access token')
    viettelpost_username = fields.Char(string='Username')
    viettelpost_passwd = fields.Char(string='Password')
    viettelpost_print_token = fields.Char(string='Print token')
    viettelpost_default_service_type = fields.Selection(_get_viettelpost_service_types, string='ViettelPost Service Type', default='VCN')
    viettelpost_product_type = fields.Selection(_viettelpost_product_types, string='ViettelPost Product Type', default='HH')
    viettelpost_national_type = fields.Selection(_viettelpost_national_types, string='ViettelPost National Type', default='1')
    viettelpost_order_payment = fields.Selection(_viettelpost_order_payments, string='ViettelPost Order Payment', default='1')

    def get_access_token(self):
        self.ensure_one()
        superself = self.sudo()
        srm = ViettelPostRequest(superself.viettelpost_token, self.prod_environment)
        data = srm.get_access_token(superself.viettelpost_username, superself.viettelpost_passwd)
        if data.get('error_message'):
            raise UserError(data.get('error_message'))
        superself.viettelpost_token = data['data']['token']

    def get_viettelpost_stores(self):
        self.ensure_one()
        superself = self.sudo()
        srm = ViettelPostRequest(superself.viettelpost_token, self.prod_environment)
        data = srm.get_stores()
        if data.get('error_message'):
            raise UserError(data.get('error_message'))
        stores = data.get('data', [])
        stores_dictionary = {str(d['groupaddressId']): {'group_address_id': d['groupaddressId'], 'customer_id': d['cusId'], 'name': d['name'], 'phone': d['phone'], 'address': d['address']} for d in stores}

        self.env['viettelpost.store'].search([]).unlink()
        self.env['viettelpost.store'].create(stores_dictionary.values())

    # ==============
    #
    # ==============

    def viettelpost_rate_shipment(self, order):
        superself = self.sudo()
        srm = ViettelPostRequest(superself.viettelpost_token, self.prod_environment)
        ship_from = order.warehouse_id.partner_id
        ship_to = order.partner_shipping_id

        check_value = srm.check_required_value(self, order, ship_from, ship_to)
        if check_value:
            return {'success': False, 'price': 0.0, 'error_message': check_value, 'warning_message': False}

        result = srm.get_shipping_price(order=order, carrier=self, ship_from=ship_from, ship_to=ship_to)

        if result.get('error_message'):
            return {'success': False, 'price': 0.0, 'error_message': result.get('error_message'), 'warning_message': False}

        if order.currency_id != self.currency_id:
            price = self.currency_id._convert(result['data']['MONEY_TOTAL_OLD'], order.currency_id, order.company_id, order.date_order or fields.Date.today())
        else:
            price = result['data']['MONEY_TOTAL_OLD']

        return {'success': True, 'price': price, 'error_message': False, 'warning_message': False}

    def viettelpost_send_shipping(self, pickings):
        superself = self.sudo()
        srm = ViettelPostRequest(superself.viettelpost_token, self.prod_environment)
        res = []
        for picking in pickings:
            carrier = picking.carrier_id
            order = picking.sale_id
            ship_from = picking.picking_type_id.warehouse_id.partner_id
            ship_to = picking.partner_id
            check_result = srm.check_required_value(carrier, order, ship_from, ship_to)
            if check_result:
                raise UserError(check_result)
            data = srm.send_shipping(carrier, order, ship_from, ship_to, picking)
            res += [{'exact_price': float(data['data']['MONEY_TOTAL']), 'tracking_number': data['data']['ORDER_NUMBER']}]
        return res

    def viettelpost_get_tracking_link(self, picking):
        return 'https://viettelpost.vn/thong-tin-don-hang?peopleTracking=sender&orderNumber=' + picking.carrier_tracking_ref

    def viettelpost_cancel_shipment(self, picking):
        superself = self.sudo()
        srm = ViettelPostRequest(superself.viettelpost_token, self.prod_environment)
        srm.cancel_shipment(picking.carrier_tracking_ref)

    def _viettelpost_convert_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_gram'), round=False)
