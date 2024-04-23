from odoo import api, fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'
    _description = 'Delivery Carrier Selection Wizard'

    def _get_viettelpost_service_types(self):
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
            # ('V510', 'Dịch vụ 5+ gói 1000g'),
            # ('V02', 'TMDT Phát nhanh 2h'),
            # ('V520', 'Dịch vụ 5+ gói 2000g'),
            # ('VCBO', 'Chuyển phát đường bộ'),
            # ('VCBA', 'Chuyển phát đường bay'),
            # ('LSTD', 'Hàng nặng nhanh'),
            # ('V505', 'Dịch vụ 5+ gói 500g'),
            # ('PTTT', 'Phân tích thị trường'),
            # ('NCOD', 'Chuyển phát nhanh'),
            # ('SCOD', 'SCOD Giao hàng thu tiền'),
            # ('PTN', 'Nội tỉnh nhanh'),
            # ('V30', 'V30'),
            # ('V25', 'V25'),
            # ('PHS', 'Nội tỉnh tiết kiệm'),
            # ('V20', 'V20'),
            # ('V35', 'V35'),
            # ('VCN', 'Tài liệu nhanh'),
            # ('V24', 'Đồng giá 24K'),
            # ('LECO', 'Hàng nặng tiết kiệm'),
            # ('VTK', 'Tài liệu tiết kiệm'),
            # ('V60', 'V60 Dịch vụ Nhanh 60h'),
            # ('VHT', 'Hỏa tốc, hẹn giờ'),
            # ('VBS', 'VBS Nhanh theo hộp'),
            # ('VBE', 'VBE Tiết kiệm theo hộp'),
            # ('LCOD', 'Chuyển phát tiêu chuẩn'),
            # ('ECOD', 'ECOD Giao hành thu tiền tiết kiệm'),
            # ('DHC', 'DHL Chuyển phát quốc tế'),
            # ('UPS', 'UPS quốc tế chỉ định'),
            # ('VQN', 'VQN Quốc tế nhanh'),
            # ('VQE', 'VQE Quốc tế chuyên tuyến'),
            # ('VVC', 'VVC Giao voucher thu tiền'),
            # ('VCT', 'VCT Chuyển tiền nhận tại địa chỉ'),
        ]

    def _viettelpost_product_types(self):
        return [('TH', 'Envelope'), ('HH', 'Goods')]

    def _viettelpost_national_types(self):
        return [('1', 'Inland'), ('0', 'International')]

    viettelpost_product_type = fields.Selection(_viettelpost_product_types, string='ViettelPost Product Type', default='HH')
    viettelpost_national_type = fields.Selection(_viettelpost_national_types, string='ViettelPost National Type', default='1')
    viettelpost_default_service_type = fields.Selection(_get_viettelpost_service_types, string='ViettelPost Service Type')

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        super()._onchange_carrier_id()
        if self.delivery_type == 'viettelpost':
            self.viettelpost_default_service_type = self.carrier_id.viettelpost_default_service_type

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
