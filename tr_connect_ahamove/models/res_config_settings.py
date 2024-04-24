# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import ustr
from odoo.exceptions import UserError
from .api_request import req


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_connect_ahamove = fields.Boolean("Connect to Ahamove")
    api_key_ahamove = fields.Char("Api Key")
    mobile = fields.Char("Mobile")
    payment_method = fields.Selection([
        ('CASH', 'CASH'),
        ('BALANCE', 'BALANCE')
        ], 'Payment Method Ahamove', copy=False, default='CASH')
    promo_code = fields.Char("Promo Code")
    percentage_fee = fields.Integer('Percentage Fee')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            auto_connect_ahamove=self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.auto_connect_ahamove'),
            api_key_ahamove=self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.api_key_ahamove'),
            mobile=self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.mobile'),
            payment_method=self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.payment_method'),
            promo_code=self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.promo_code'),
            percentage_fee=self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.percentage_fee')
        )
        return res

    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('tr_custom_field.auto_connect_ahamove', self.auto_connect_ahamove)
        ICPSudo.set_param('tr_custom_field.api_key_ahamove', self.api_key_ahamove)
        ICPSudo.set_param('tr_custom_field.mobile', self.mobile)
        ICPSudo.set_param('tr_custom_field.payment_method', self.payment_method)
        ICPSudo.set_param('tr_custom_field.promo_code', self.promo_code)
        ICPSudo.set_param('tr_custom_field.percentage_fee', self.percentage_fee)
        super(ResConfigSettings, self).set_values()


class Company(models.Model):
    _inherit = "res.company"

    token_aha = fields.Char(string='Token')
    ahamove_refresh_token = fields.Char(string='Refresh Token')
    ahamove_api_key = fields.Char(string='API Key')
    ahamove_phone = fields.Char(string='Phone')

    def _validate_data(self):
        if not self.ahamove_api_key:
            raise UserError(_('The field API Key is required.'))
        elif not self.ahamove_phone:
            raise UserError(_('The field Phone is required.'))

    def button_set_token_aha(self):
        self.ensure_one()
        self._validate_data()
        params = {
            'mobile': self.ahamove_phone,
            'name': 'FriendShip',
            'api_key': self.ahamove_api_key
        }
        try:
            api_url = 'https://api.ahamove.com/v1/partner/register_account'
            response = req(api_url, 'GET', params)
        except Exception as e:
            raise UserError(_(f'[Ahamove] - Call API Register Account Exception. {ustr(e)}'))
        if response:
            self.sudo().write({
                'token_aha': response.get('token'),
                'ahamove_refresh_token': response.get('refresh_token')
            })