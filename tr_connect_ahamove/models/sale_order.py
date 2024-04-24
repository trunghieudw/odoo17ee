# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import requests
import socket
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_method = fields.Selection([
        ('online', 'Không thu COD'),
        ('cod', 'Có thu COD')],
        string='Payment methods',
        default='cod', required=True)
    service_ahamove = fields.Selection([
        ('SGN-BIKE', 'Sai Gon Bike'),
        ('SGN-SAMEDAY', 'Ahamove 4H SGN'),
        ('HAN-BIKE', 'Ha Noi Bike'),
        ('VCA-BIKE', 'Can Tho Bike'),
        ('DAD-BIKE', 'Da Nang Bike'),
        ('SGN-VAN-1000', 'Sai Gon VAN1000'),
        ('HAN-VAN-1000', 'Ha Noi VAN1000')],
        default='SGN-BIKE', required=True)

    def calculated_shipping_fee(self):
        """
        Calculated shipping fee to Ahamove
        """
        for so in self:
            header = 'https://api.ahamove.com/v1/order/estimated_fee?token='

            # payment_method = self.env['ir.config_parameter'].sudo().get_param(
            #     'tr_custom_field.payment_method')
            # promo_code = self.env['ir.config_parameter'].sudo().get_param(
            #     'tr_custom_field.promo_code')
            # if not payment_method:
            #     raise UserError(_("Please choose a payment method for ahamove!"))

            rail = f'&service_id={so.service_ahamove}&requests=[]'
            token = self.env.company.token_aha
            if not token:
                raise UserError(_("Please register to get tokens on ahamove!"))

            if not so.warehouse_id.partner_id:
                raise UserError(_("Please set partner for this Sale order!"))
            add_sender = '{"address"' + ":" + '"' + so.warehouse_id.partner_id.street + '",' + '"mobile"' + ":" + '"' + so.warehouse_id.partner_id.phone + '"' + '}'
            if so.partner_id.mobile:
                add_receiver = '{"address"' + ":" + '"' + so.partner_id.street + '",' + '"mobile"' + ":" + '"' + so.partner_id.mobile + '"' + '}'
            elif so.partner_id.phone:
                add_receiver = '{"address"' + ":" + '"' + so.partner_id.street + '",' + '"mobile"' + ":" + '"' + so.partner_id.phone + '"' + '}'
            else:
                raise UserError(
                    _('Please enter the phone number for the customer:%s that you want to order on ahamove!!!',
                      so.partner_id.name))

            # Post Url to Estimate Order Fee
            url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + rail
            print("url", url)
            try:
                res = requests.post(url)
                _logger.info('API URL : %s', url)
                _logger.info('Response Status code : %s', res.status_code)
                if res.status_code != 200:
                    raise UserError(_('Calculated fee ship failed, please check again.'))
            except (socket.gaierror, socket.error, socket.timeout) as err:
                raise UserError(_('A network error caused the failure of the job: %s', err))
            except Exception:
                raise UserError(_("Calculated fee ship error.Please try again or notify admin for more details!"))
            if res and res.status_code == 200:
                data = res.json()
                print("Estimate Order Fee >>>>>>>>>>>>>>>> data", data)
                print("status code----------------------", res.status_code)

                message_fee_id = self.env['popup.message.fee'].create({'fee': data.get('total_price')})
                return {
                    'name': 'Fee Shipping',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'popup.message.fee',
                    'res_id': message_fee_id.id,
                    'target': 'new'
                }
