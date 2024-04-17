from odoo import fields, models, api


class MessageZaloCompose(models.TransientModel):
    _name = 'message.zalo.compose'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Khách hàng')
    phone = fields.Char('Số điện thoại')
    message = fields.Text('Nội dung')

    def send_message(self):
        print('test')
