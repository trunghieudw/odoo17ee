# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import requests
import logging
import socket

from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class PopupBookingAhamove(models.TransientModel):
    _name = 'popup.booking.ahamove'
    _description = "Popup booking ahamove"

    service_ahamove = fields.Selection([
        ('SGN-EXPRESS', 'Sai Gon Bike'),
        ('SGN-SAMEDAY', 'Ahamove 4H SGN'),
        ('HAN-BIKE', 'Ha Noi Bike'),
        ('VCA-BIKE', 'Can Tho Bike'),
        ('DAD-BIKE', 'Da Nang Bike'),
        ('SGN-VAN-1000', 'Sai Gon VAN1000'),
        ('HAN-VAN-1000', 'Ha Noi VAN1000')],
        default='SGN-EXPRESS', required=True)
    payment_method = fields.Selection([
        ('online', 'Không thu COD'),
        ('cod', 'Có thu COD')],
        string='Phương thức thanh toán',
        default='online', required=True)
    cod = fields.Integer(string='Số tiền thu COD', required=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Kho hàng', required=True)
    phone = fields.Char()
    mobile = fields.Char()
    street = fields.Char()
    payment = fields.Selection([
        ('CASH', 'CASH'),
        ('BALANCE', 'BALANCE')
    ], 'Thanh toán', copy=False, default='CASH', required=True)
    merchandises = fields.Selection([
        ('TIER_1', 'Tiêu chuẩn'),
        ('TIER_2', 'Mức 1'),
        ('TIER_3', 'Mức 2'),
        ('TIER_4', 'Mức 3')],
        default='TIER_1', required=True)
    back = fields.Boolean("Back to pick up point")
    note = fields.Text('Note')

    def confirm_booking_ahamove(self):
        """
        Create order to Ahamove
        """
        for booking in self:
            active_id = self.env.context.get('active_id')
            picking = self.env['stock.picking'].search([('id', '=', active_id)])
            if picking.tr_ahamove_ids:
                if any(ahamove.tr_status not in ['CANCELLED', 'FAILED', 'COMPLETED'] for ahamove in
                       picking.tr_ahamove_ids):
                    raise UserError(_("Can't create a new order because there's an order in progress!"))
                header = 'https://api.ahamove.com/v1/order/create?token='

                payment_method = booking.payment
                promo_code = self.env['ir.config_parameter'].sudo().get_param(
                    'tr_custom_field.promo_code')
                if not payment_method:
                    raise UserError(_("Please choose a payment method for ahamove!"))

                id_1 = ""
                price = ["10000", "20000", "40000"]
                if booking.merchandises != 'TIER_1':
                    service_request_1 = booking.service_ahamove + "-BULKY"
                    if booking.merchandises == 'TIER_2':
                        id_1 = '{"_id"' + ":" + '"' + service_request_1 + '",' + '"price"' + ":" + price[0] + ',' + '"tier_code"' + ":" + '"' + booking.merchandises + '"' + '}'
                    elif booking.merchandises == 'TIER_3':
                        id_1 = '{"_id"' + ":" + '"' + service_request_1 + '",' + '"price"' + ":" + price[1] + ',' + '"tier_code"' + ":" + '"' + booking.merchandises + '"' + '}'
                    else:
                        id_1 = '{"_id"' + ":" + '"' + service_request_1 + '",' + '"price"' + ":" + price[2] + ',' + '"tier_code"' + ":" + '"' + booking.merchandises + '"' + '}'
                id_2 = ""
                if booking.back:
                    service_request_2 = booking.service_ahamove + "-ROUND-TRIP"
                    id_2 = '{"_id"' + ":" + '"' + service_request_2 + '"}'

                if id_1 and id_2:
                    rail = f'&service_id={booking.service_ahamove}&requests=[{id_1},{id_2}]&payment_method={payment_method}&promo_code={promo_code}'
                elif id_1:
                    rail = f'&service_id={booking.service_ahamove}&requests=[{id_1}]&payment_method={payment_method}&promo_code={promo_code}'
                elif id_2:
                    rail = f'&service_id={booking.service_ahamove}&requests=[{id_2}]&payment_method={payment_method}&promo_code={promo_code}'
                else:
                    rail = f'&service_id={booking.service_ahamove}&requests=[]&payment_method={payment_method}&promo_code={promo_code}'

                token = self.env.company.token_aha
                if not token:
                    raise UserError(_("Please register to get tokens on ahamove!"))

                cod = str(int(booking.cod))
                if not picking.picking_type_id.warehouse_id.partner_id:
                    raise UserError(_("Please set partner for this picking!"))
                add_sender = '{"address"' + ":" + '"' + booking.warehouse_id.partner_id.street + '",' + '"mobile"' + ":" + '"' + booking.warehouse_id.partner_id.phone + '"' + '}'

                if booking.payment_method == "cod":
                    if booking.mobile:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.mobile + '",' + '"cod"' + ":" + cod + '}'
                    elif booking.phone:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.phone + '",' + '"cod"' + ":" + cod + '}'
                    else:
                        raise UserError(
                            _('Please enter the phone number for the customer:%s that you want to order on ahamove!!!',
                              picking.partner_id.name))
                else:
                    if booking.mobile:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.mobile + '"' + '}'
                    elif booking.phone:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.phone + '"' + '}'
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

                # Post Url to create order
                url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + rail
                # url = header + token + f'&order_time=0&path=[{add_sender},{add_receiver}]' + f'&items={items}' + rail
                print("url----------------------------------", url)
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
            else:
                header = 'https://api.ahamove.com/v1/order/create?token='

                payment_method = booking.payment
                promo_code = self.env['ir.config_parameter'].sudo().get_param(
                    'tr_custom_field.promo_code')
                if not payment_method:
                    raise UserError(_("Please choose a payment method for ahamove!"))

                id_1 = ""
                price = ["10000", "20000", "40000"]
                if booking.merchandises != 'TIER_1':
                    service_request_1 = booking.service_ahamove + "-BULKY"
                    if booking.merchandises == 'TIER_2':
                        id_1 = '{"_id"' + ":" + '"' + service_request_1 + '",' + '"price"' + ":" + price[0] + ',' + '"tier_code"' + ":" + '"' + booking.merchandises + '"' + '}'
                    elif booking.merchandises == 'TIER_3':
                        id_1 = '{"_id"' + ":" + '"' + service_request_1 + '",' + '"price"' + ":" + price[1] + ',' + '"tier_code"' + ":" + '"' + booking.merchandises + '"' + '}'
                    else:
                        id_1 = '{"_id"' + ":" + '"' + service_request_1 + '",' + '"price"' + ":" + price[2] + ',' + '"tier_code"' + ":" + '"' + booking.merchandises + '"' + '}'
                id_2 = ""
                if booking.back:
                    service_request_2 = booking.service_ahamove + "-ROUND-TRIP"
                    id_2 = '{"_id"' + ":" + '"' + service_request_2 + '"}'

                if id_1 and id_2:
                    rail = f'&service_id={booking.service_ahamove}&requests=[{id_1},{id_2}]&payment_method={payment_method}&promo_code={promo_code}'
                elif id_1:
                    rail = f'&service_id={booking.service_ahamove}&requests=[{id_1}]&payment_method={payment_method}&promo_code={promo_code}'
                elif id_2:
                    rail = f'&service_id={booking.service_ahamove}&requests=[{id_2}]&payment_method={payment_method}&promo_code={promo_code}'
                else:
                    rail = f'&service_id={booking.service_ahamove}&requests=[]&payment_method={payment_method}&promo_code={promo_code}'
                token = self.env.company.token_aha
                if not token:
                    raise UserError(_("Please register to get tokens on ahamove!"))

                cod = str(int(booking.cod))

                if not picking.picking_type_id.warehouse_id.partner_id:
                    raise UserError(_("Please set partner for this picking!"))
                add_sender = '{"address"' + ":" + '"' + booking.warehouse_id.partner_id.street + '",' + '"mobile"' + ":" + '"' + booking.warehouse_id.partner_id.phone + '"' + '}'

                if booking.payment_method == "cod":
                    if booking.mobile:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.mobile + '",' + '"cod"' + ":" + cod + '}'
                    elif booking.phone:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.phone + '",' + '"cod"' + ":" + cod + '}'
                    else:
                        raise UserError(
                            _('Please enter the phone number for the customer:%s that you want to order on ahamove!!!',
                              picking.partner_id.name))
                else:
                    if booking.mobile:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.mobile + '"' + '}'
                    elif booking.phone:
                        add_receiver = '{"address"' + ":" + '"' + booking.street + '",' + '"mobile"' + ":" + '"' + booking.phone + '"' + '}'
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
                print("url---------------------------------", url)
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
