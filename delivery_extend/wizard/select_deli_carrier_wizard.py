from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SelectDeliveryCarrierWizard(models.TransientModel):
    _name = 'select.delivery.carrier.wizard'
    _description = 'This module is used open a popup to select delivery carrier'

    @api.model
    def default_get(self, fields_list):
        values = super(SelectDeliveryCarrierWizard, self).default_get(fields_list)
        if not values.get('deli_order_id') and 'active_model' in self._context and\
                self._context['active_model'] == 'stock.picking':
            values['deli_order_id'] = self._context.get('active_id')
        return values

    deli_order_id = fields.Many2one('stock.picking', required=True, readonly=True)
    deli_carrier_id = fields.Many2one('delivery.carrier', required=True)

    def action_fill_shipment_info(self):
        if self.deli_carrier_id.delivery_type == 'deli_boys':
            return {
                'name': _('Delivery Boys Shipment Information'),
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('delivery_extend.booking_delivery_boys_wizard_form_view').id,
                'res_model': 'booking.delivery.boys.wizard',
                'context': {
                    'default_deli_order_id': self.deli_order_id.id,
                    'default_warehouse_id': self.deli_order_id.picking_type_id.warehouse_id.id,
                    'default_deli_carrier_id': self.deli_carrier_id.id,
                    'default_receiver_id': self.deli_order_id.partner_id.id,
                    'default_receiver_phone': self.deli_order_id.partner_id.phone,
                    'default_receiver_street': self.deli_order_id.partner_id.street,
                    'default_receiver_ward_id': self.deli_order_id.partner_id.ward_id.id,
                    'default_receiver_district_id': self.deli_order_id.partner_id.district_id.id,
                    'default_receiver_province_id': self.deli_order_id.partner_id.city_id.id,
                    'default_cod': self.deli_order_id.sale_id.amount_due
                },
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        elif self.deli_carrier_id.delivery_type == 'viettelpost':
            return {
                'name': _('Viettelpost Shipment Information'),
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('delivery_extend.booking_viettelpost_wizard_form_view').id,
                'res_model': 'booking.viettelpost.wizard',
                'context': {
                    'default_deli_order_id': self.deli_order_id.id,
                    'default_deli_carrier_id': self.deli_carrier_id.id,
                    'default_receiver_id': self.deli_order_id.partner_id.id,
                    'default_receiver_phone': self.deli_order_id.partner_id.phone,
                    'default_receiver_street': self.deli_order_id.partner_id.street,
                    'default_receiver_ward_id': self.deli_order_id.partner_id.ward_id.id,
                    'default_receiver_district_id': self.deli_order_id.partner_id.district_id.id,
                    'default_receiver_province_id': self.deli_order_id.partner_id.city_id.id,
                    'default_warehouse_id': self.deli_order_id.picking_type_id.warehouse_id.id,
                    'default_sender_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.id,
                    'default_sender_phone': self.deli_order_id.picking_type_id.warehouse_id.partner_id.phone,
                    'default_sender_street': self.deli_order_id.picking_type_id.warehouse_id.partner_id.street,
                    'default_sender_ward_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.ward_id.id,
                    'default_sender_district_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.district_id.id,
                    'default_sender_province_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.city_id.id,
                    'default_cod': self.deli_order_id.sale_id.amount_due
                },
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        elif self.deli_carrier_id.delivery_type == 'ahamove':
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'context': {
                    'default_deli_order_id': self.deli_order_id.id,
                    'default_deli_carrier_id': self.deli_carrier_id.id,
                    'default_receiver_id': self.deli_order_id.partner_id.id,
                    'default_receiver_phone': self.deli_order_id.partner_id.phone,
                    'default_receiver_street': self.deli_order_id.partner_id.street,
                    'default_receiver_ward_id': self.deli_order_id.partner_id.ward_id.id,
                    'default_receiver_district_id': self.deli_order_id.partner_id.district_id.id,
                    'default_receiver_province_id': self.deli_order_id.partner_id.city_id.id,
                    'default_warehouse_id': self.deli_order_id.picking_type_id.warehouse_id.id,
                    'default_sender_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.id,
                    'default_sender_phone': self.deli_order_id.picking_type_id.warehouse_id.partner_id.phone,
                    'default_sender_street': self.deli_order_id.picking_type_id.warehouse_id.partner_id.street,
                    'default_sender_ward_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.ward_id.id,
                    'default_sender_district_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.district_id.id,
                    'default_sender_province_id': self.deli_order_id.picking_type_id.warehouse_id.partner_id.city_id.id,
                    'default_cod': self.deli_order_id.sale_id.amount_due
                },
                'view_id': self.env.ref('delivery_extend.booking_ahamove_wizard_form_view').id,
                'res_model': 'booking.ahamove.wizard',
                'target': 'new'
            }
        else:
            raise ValidationError(_(f'Delivery carrier {self.deli_carrier_id.delivery_type} not found.'))