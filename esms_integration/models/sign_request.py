from odoo import models, _
from odoo.exceptions import UserError


class SignRequestItem(models.Model):
    _inherit = 'sign.request.item'
    _description = 'Signature Request Item'

    def _send_sms(self):
        sms_auth_content = self.env['ir.config_parameter'].sudo().get_param('sms_auth_content', False)
        if not sms_auth_content:
            raise UserError(_('The SMS authentication not found.'))
        for rec in self:
            rec._reset_sms_token()
            content = sms_auth_content.format(otp=rec.sms_token, expire=1, path='sign/help')
            self.env['esms.api']._send_esms([rec.sms_number], content, 'send_cus_care_post')
