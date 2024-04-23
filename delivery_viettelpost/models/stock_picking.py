from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .viettelpost_request import ViettelPostRequest


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    viettelpost_store_id = fields.Many2one('viettelpost.store', tracking=True)
    viettelpost_default_service_type = fields.Selection(_get_viettelpost_service_types, string='ViettelPost Service Type', default='VCN')
    viettelpost_product_type = fields.Selection(_viettelpost_product_types, string='ViettelPost Product Type', default='HH')
    viettelpost_national_type = fields.Selection(_viettelpost_national_types, string='ViettelPost National Type', default='1')
    viettelpost_order_payment = fields.Selection(_viettelpost_order_payments, string='ViettelPost Order Payment', default='1')

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        if self.delivery_type == 'viettelpost':
            self.viettelpost_default_service_type = self.carrier_id.viettelpost_default_service_type
            self.viettelpost_product_type = self.carrier_id.viettelpost_product_type
            self.viettelpost_national_type = self.carrier_id.viettelpost_national_type
            self.viettelpost_order_payment = self.carrier_id.viettelpost_order_payment

    @api.onchange('viettelpost_default_service_type')
    def _onchange_viettelpost_default_service_type(self):
        if self.delivery_type == 'viettelpost':
            self.carrier_id.write({'viettelpost_default_service_type': self.viettelpost_default_service_type})

    @api.onchange('viettelpost_product_type')
    def _onchange_viettelpost_product_type(self):
        if self.delivery_type == 'viettelpost':
            self.carrier_id.write({'viettelpost_product_type': self.viettelpost_product_type})

    @api.onchange('viettelpost_national_type')
    def _onchange_viettelpost_national_type(self):
        if self.delivery_type == 'viettelpost':
            self.carrier_id.write({'viettelpost_national_type': self.viettelpost_national_type})

    def action_open_viettelpost_print(self):
        superself = self.sudo()
        srm = ViettelPostRequest(superself.carrier_id.viettelpost_token, self.carrier_id.prod_environment)
        data = srm.get_link_print(self.carrier_tracking_ref, superself.carrier_id.viettelpost_print_token)
        if data.get('error_message'):
            raise UserError(data.get('error_message'))
        else:
            url = data['message']
            return {'type': 'ir.actions.act_url', 'url': url}
