# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .api_request import req
import requests
import logging
import socket

from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    service_ahamove = fields.Selection([
        ('SGN-BIKE', 'Sai Gon Bike'),
        ('SGN-SAMEDAY', 'Ahamove 4H'),
        ('HAN-BIKE', 'Ha Noi Bike'),
        ('VCA-BIKE', 'Can Tho Bike'),
        ('DAD-BIKE', 'Da Nang Bike'),
        ('SGN-VAN-1000', 'Sai Gon VAN1000'),
        ('HAN-VAN-1000', 'Ha Noi VAN1000')],
        default='SGN-BIKE', required=True)

    tr_ahamove_ids = fields.One2many('tr.ahamove', 'tr_picking_id', string='Ahamove Order')
    order_ahamove = fields.Char(compute='_compute_order_ahamove', string='Order Ahamove Completed', readonly=True)

    def _compute_order_ahamove(self):
        self.order_ahamove = ""
        for picking in self:
            if picking.tr_ahamove_ids:
                for ahamove_id in picking.tr_ahamove_ids:
                    if ahamove_id.tr_status == 'COMPLETED':
                        picking.order_ahamove = ahamove_id.name

    def booking_ahamove(self):
        """
        Create order to Ahamove
        """
        for picking in self:
            if picking.tr_ahamove_ids:
                if any(ahamove.tr_status not in ['CANCELLED', 'FAILED', 'COMPLETED'] for ahamove in picking.tr_ahamove_ids):
                    raise UserError(_("Can't create a new order because there's an order in progress!"))
                header = 'https://api.ahamove.com/v1/order/create?token='

                payment_method = self.env['ir.config_parameter'].sudo().get_param(
                    'tr_custom_field.payment_method')
                promo_code = self.env['ir.config_parameter'].sudo().get_param(
                    'tr_custom_field.promo_code')
                if not payment_method:
                    raise UserError(_("Please choose a payment method for ahamove!"))

                rail = f'&service_id={picking.service_ahamove}&requests=[]&payment_method={payment_method}&promo_code={promo_code}'
                token = self.env.company.token_aha
                if not token:
                    raise UserError(_("Please register to get tokens on ahamove!"))

                cod = ""
                if picking.sale_id:
                    if picking.sale_id.payment_method == 'cod':
                        cod = str(int(picking.sale_id.amount_total))

                if not picking.picking_type_id.warehouse_id.partner_id:
                    raise UserError(_("Please set partner for this picking!"))
                add_sender = '{"address"' + ":" + '"' + picking.picking_type_id.warehouse_id.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.picking_type_id.warehouse_id.partner_id.phone + '"' + '}'

                if cod:
                    if picking.partner_id.mobile:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.mobile + '",' + '"cod"' + ":" + cod + '}'
                    elif picking.partner_id.phone:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.phone + '",' + '"cod"' + ":" + cod + '}'
                    else:
                        raise UserError(_('Please enter the phone number for the customer:%s that you want to order on ahamove!!!', picking.partner_id.name))
                else:
                    if picking.partner_id.mobile:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.mobile + '"' + '}'
                    elif picking.partner_id.phone:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.phone + '"' + '}'
                    else:
                        raise UserError(_('Please enter the phone number for the customer:%s that you want to order on ahamove!!!',picking.partner_id.name))

                # items = []
                # for move_line in picking.move_line_ids_without_package:
                #     item_temp = {
                #         "_id": move_line.product_id.id,
                #         "num": move_line.qty_done,
                #         "name": move_line.product_id.name,
                #         "price": move_line.product_id.lst_price
                #     }
                #     if item_temp:
                #         items.append(item_temp)

                # Post Url to create order
                url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + rail
                # url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + f'&items={items}' + rail
                print("url", url)
                try:
                    res = requests.post(url)
                    _logger.info('API URL : %s', url)
                    _logger.info('Response Status code : %s', res.status_code)
                    if res.status_code != 200:
                        raise UserError(_('Order creation failed, please check again.'))
                except (socket.gaierror, socket.error, socket.timeout) as err:
                    raise UserError(_('A network error caused the failure of the job: %s', err))
                except Exception:
                    raise UserError(_("Create Order error.Please try again or notify admin for more details!"))
                # for picking in self:
                if res and res.status_code == 200:
                    data = res.json()
                    print("order created >>>>>>>>>>>>>>>> data", data)
                    print("status code----------------------", res.status_code)
                    tr_ahamove = self.env['tr.ahamove']
                    value = {
                        'name': data.get('order_id'),
                        'tr_picking_id': picking.id,
                        'tr_fee': data.get('order').get('total_pay'),
                        'tr_total_fee': data.get('order').get('total_price'),
                        'shared_link': data.get('shared_link'),
                        'tr_address_sender': data.get('order').get('path')[0].get('address'),
                        'tr_address_receiver': data.get('order').get('path')[1].get('address'),
                    }
                    if data.get('order').get('path')[1].get('cod'):
                        value.update({"tr_cod": data.get('order').get('path')[1].get('cod')})
                    if data.get('status'):
                        if data.get('status') == 'IN PROCESS':
                            value.update({"tr_status": "IN_PROCESS"})
                        else:
                            value.update({"tr_status": data.get('status')})
                    if value:
                        tr_ahamove_id = tr_ahamove.sudo().create(value)
                        message_id = self.env['popup.message'].create({'message': 'You have successfully created an order.'})
                        return {
                            'name': 'Message',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'popup.message',
                            'res_id': message_id.id,
                            'target': 'new'
                        }
            else:
                header = 'https://api.ahamove.com/v1/order/create?token='

                payment_method = self.env['ir.config_parameter'].sudo().get_param(
                    'tr_custom_field.payment_method')
                promo_code = self.env['ir.config_parameter'].sudo().get_param(
                    'tr_custom_field.promo_code')
                if not payment_method:
                    raise UserError(_("Please choose a payment method for ahamove!"))

                rail = f'&service_id={picking.service_ahamove}&requests=[]&payment_method={payment_method}&promo_code={promo_code}'

                token = self.env.company.token_aha
                if not token:
                    raise UserError(_("Please register to get tokens on ahamove!"))

                cod = ""
                if picking.sale_id:
                    if picking.sale_id.payment_method == 'cod':
                        cod = str(int(picking.sale_id.amount_total))

                if not picking.picking_type_id.warehouse_id.partner_id:
                    raise UserError(_("Please set partner for this picking!"))
                add_sender = '{"address"' + ":" + '"' + picking.picking_type_id.warehouse_id.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.picking_type_id.warehouse_id.partner_id.phone + '"' + '}'

                if cod:
                    if picking.partner_id.mobile:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.mobile + '",' + '"cod"' + ":" + cod + '}'
                    elif picking.partner_id.phone:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.phone + '",' + '"cod"' + ":" + cod + '}'
                    else:
                        raise UserError(
                            _('Please enter the phone number for the customer:%s that you want to order on ahamove!!!',
                              picking.partner_id.name))
                else:
                    if picking.partner_id.mobile:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.mobile + '"' + '}'
                    elif picking.partner_id.phone:
                        add_receiver = '{"address"' + ":" + '"' + picking.partner_id.street + '",' + '"mobile"' + ":" + '"' + picking.partner_id.phone + '"' + '}'
                    else:
                        raise UserError(
                            _('Please enter the phone number for the customer:%s that you want to order on ahamove!!!',
                              picking.partner_id.name))

                # items = []
                # for move_line in picking.move_line_ids_without_package:
                #     item_temp = {
                #         "_id": move_line.product_id.id,
                #         "num": move_line.qty_done,
                #         "name": move_line.product_id.name,
                #         "price": move_line.product_id.lst_price
                #     }
                #     if item_temp:
                #         items.append(item_temp)

                # Post Url to get rate
                url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + rail
                # url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + f'&items={items}' + rail
                print("url", url)
                try:
                    res = requests.post(url)
                    _logger.info('API URL : %s', url)
                    _logger.info('Response Status code : %s', res.status_code)
                    if res.status_code != 200:
                        raise UserError(_('Order creation failed, please check again.'))
                except (socket.gaierror, socket.error, socket.timeout) as err:
                    raise UserError(_('A network error caused the failure of the job: %s', err))
                except Exception:
                    raise UserError(_("Create Order error.Please try again or notify admin for more details!"))
                # for picking in self:
                if res and res.status_code == 200:
                    data = res.json()
                    print("order created >>>>>>>>>>>>>>>> data", data)
                    print("status code----------------------", res.status_code)
                    tr_ahamove = self.env['tr.ahamove']
                    value = {
                        'name': data.get('order_id'),
                        'tr_picking_id': picking.id,
                        'tr_fee': data.get('order').get('total_pay'),
                        'tr_total_fee': data.get('order').get('total_price'),
                        'shared_link': data.get('shared_link'),
                        'tr_address_sender': data.get('order').get('path')[0].get('address'),
                        'tr_address_receiver': data.get('order').get('path')[1].get('address'),
                    }

                    if data.get('order').get('path')[1].get('cod'):
                        value.update({"tr_cod": data.get('order').get('path')[1].get('cod')})

                    if data.get('status'):
                        if data.get('status') == 'IN PROCESS':
                            value.update({"tr_status": "IN_PROCESS"})
                        else:
                            value.update({"tr_status": data.get('status')})
                    if value:
                        tr_ahamove_id = tr_ahamove.sudo().create(value)
                        message_id = self.env['popup.message'].create(
                            {'message': 'You have successfully created an order.'})
                        return {
                            'name': 'Message',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'popup.message',
                            'res_id': message_id.id,
                            'target': 'new'
                        }

    def cancel_booking_ahamove(self):
        """
        Cancel order to Ahamove
        """
        for picking in self:
            if any(ahamove.tr_status not in ['CANCELLED', 'FAILED', 'COMPLETED', 'BOARDED', 'COMPLETING', 'IN_PROCESS'] for ahamove in picking.tr_ahamove_ids):
                for ahamove in picking.tr_ahamove_ids:
                    if ahamove.tr_status in ['CANCELLED', 'FAILED', 'COMPLETED']:
                        continue
                    comment = "cancel"
                    if ahamove.tr_status == 'ACCEPTED':
                        comment = "We want to cancel this order, sorry for the cancellation!"
                    header = 'https://api.ahamove.com/v1/order/cancel?token='
                    token = self.env.company.token_aha
                    if not token:
                        raise UserError(_("Please register to get tokens on ahamove!"))
                    url = header + token + f'&order_id={ahamove.name}&comment={comment}'
                    try:
                        res = requests.get(url)
                        _logger.info('API URL : %s', url)
                        _logger.info('Response Status code : %s', res.status_code)
                        if res.status_code != 200:
                            raise UserError(_('Cancel order failed, please check again.'))
                    except (socket.gaierror, socket.error, socket.timeout) as err:
                        raise UserError(_('A network error caused the failure of the job: %s', err))
                    except Exception:
                        raise UserError(_("Cancel order error.Please try again or notify admin for more details!"))
                    if res and res.status_code == 200:
                        data = res.json()
                        print("order created >>>>>>>>>>>>>>>> test", data)
                        print("status code----------------------", res.status_code)
                        ahamove.write({'tr_status': 'CANCELLED'})
                        message_id = self.env['popup.message'].create({'message': 'You have successfully canceled an order.'})
                        return {
                            'name': 'Message',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'popup.message',
                            'res_id': message_id.id,
                            'target': 'new'
                        }
            else:
                raise UserError(_("There are no pending orders to cancel!!!"))

    def open_booking_ahamove(self):
        self.ensure_one()
        payment_method = self.env['ir.config_parameter'].sudo().get_param(
            'tr_custom_field.payment_method')
        context = {'default_service_ahamove': self.service_ahamove,
                   # 'default_payment_method': self.sale_id.payment_method,
                   # 'default_cod': self.sale_id.amount_total,
                   'default_warehouse_id': self.picking_type_id.warehouse_id.id,
                   'default_phone': self.partner_id.phone,
                   'default_mobile': self.partner_id.mobile,
                   'default_street': self.partner_id.street,
                   'default_payment': payment_method,}
        print("contextttttttttttttttttttttttttttt", context)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('tr_connect_ahamove.popup_booking_ahamove_wizard_form').id,
            'res_model': 'popup.booking.ahamove',
            'context': context,
            'target': 'new'
        }
