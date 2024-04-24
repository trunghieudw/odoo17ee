# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import math

class PopupMessageFee(models.TransientModel):
    _name = 'popup.message.fee'
    _description = "Show Message Fee"

    fee = fields.Float('Fee Shipping', required=True)


    def action_add_fee_ship(self):
        active_model_id = self.env.context.get('active_id')
        if active_model_id:
            sale_obj = self.env['sale.order'].search([('id', '=', active_model_id)])
            print("sale object >>>>>>>>>>>>>>>>>>>>>>>>", sale_obj, sale_obj.name)
            percentage_fee = self.env['ir.config_parameter'].sudo().get_param(
                'tr_custom_field.percentage_fee')
            total_fee_ship = self.fee + (self.fee * (float(percentage_fee) / 100))
            product = self.env['product.product'].search([('default_code', '=', 'fee_001')])
            self.env['sale.order.line'].create({
                'product_id': product.id,
                'price_unit': total_fee_ship,
                'order_id': sale_obj.id,
            })
        return {'type': 'ir.actions.act_window_close'}