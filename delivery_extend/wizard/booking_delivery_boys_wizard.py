from typing import Dict, Any
from odoo import fields, models, api, _
from odoo.tools import ustr
from odoo.exceptions import UserError


class BookingDeliveryBoysWizard(models.TransientModel):
    _name = 'booking.delivery.boys.wizard'
    _description = 'This module fills and confirms info about shipment creating handover to internal carriers.'

    def _get_default_sequence(self):
        try:
            sequence = self.env['ir.sequence'].search([
                ('code', '=', 'delivery.boys'),
                ('prefix', '=', 'DB'),
                ('name', '=', 'Delivery Boys Sequence'),
                ('active', '=', True)
            ])
            next_document = sequence.get_next_char(sequence.number_next_actual)
            self._cr.execute('''SELECT name FROM delivery_boys''')
            query_res = self._cr.fetchall()
            while next_document in [res[0] for res in query_res]:
                next_tmp = self.env['ir.sequence'].next_by_code('delivery.boys')
                next_document = next_tmp
            return next_document
        except Exception as e:
            raise UserError(_(ustr(e)))

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    name = fields.Char(string='B/L code', readonly=True, default=_get_default_sequence, required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    deli_carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier', required=True, readonly=True)

    boy_id = fields.Many2one('res.partner', 'Delivery Boy', required=True)
    boy_phone = fields.Char(string='Phone', required=True)

    receiver_id = fields.Many2one('res.partner', string='Receiver', required=True)
    receiver_phone = fields.Char(string='Phone', required=True)
    receiver_street = fields.Char(string='Street', required=True)
    receiver_ward_id = fields.Many2one('res.ward', string='Ward')
    receiver_district_id = fields.Many2one('res.district', string='District')
    receiver_province_id = fields.Many2one('res.city', string='Province')

    deli_order_id = fields.Many2one('stock.picking', string='Delivery order', required=True, readonly=True)
    fee_ship = fields.Monetary(string='Fee ship', currency_field='currency_id')
    cod = fields.Monetary(string='COD', currency_field='currency_id')
    no_of_package = fields.Integer(string='Number of package', default=1, required=True)
    est_deli = fields.Integer(string='Estimate delivery')
    weight = fields.Float(string='Weight')
    note = fields.Text(string='Note')

    @api.onchange('receiver_province_id')
    def _onchange_receiver_province_id(self):
        for rec in self:
            if rec.receiver_province_id:
                return {
                    'domain':
                        {
                            'receiver_district_id': [('city_id', '=', rec.receiver_province_id.id)]
                        },
                }

    @api.onchange('receiver_district_id')
    def _onchange_receiver_district_id(self):
        for rec in self:
            if rec.receiver_district_id:
                return {
                    'domain':
                        {
                            'receiver_ward_id': [('district_id', '=', rec.receiver_district_id.id)]
                        },
                }

    @api.onchange('boy_id')
    def _onchange_boy_id(self):
        for rec in self:
            if rec.boy_id:
                rec.boy_phone = rec.boy_id.phone

    def _get_default_hours_uom_name(self):
        return self._get_hours_uom_name()

    def _get_default_gram_uom_name(self):
        return self._get_gram_uom_name()

    hours_uom_name = fields.Char(string='Hours unit of measure label', default=_get_default_hours_uom_name,
                                 compute='_compute_hours_uom_name')

    gram_uom_name = fields.Char(string='Gram unit of measure label', default=_get_default_gram_uom_name,
                                compute='_compute_gram_uom_name')

    @api.model
    def _get_hours_uom_name(self):
        return self.env.ref('uom.product_uom_hour').display_name

    @api.model
    def _get_gram_uom_name(self):
        return self.env.ref('uom.product_uom_gram').display_name

    def _compute_hours_uom_name(self):
        for rec in self:
            rec.hours_uom_name = self._get_hours_uom_name()

    def _compute_gram_uom_name(self):
        for rec in self:
            rec.gram_uom_name = self._get_gram_uom_name()

    def _get_payload_delivery_boys(self) -> Dict[str, Any]:
        payload: dict = {
            'name': self.name,
            'deli_boy_id': self.boy_id.id,
            'deli_phone': self.boy_phone,
            'deli_order_id': self.deli_order_id.id,
            'partner_id': self.receiver_id.id,
            'partner_phone': self.receiver_phone,
            'street': self.receiver_street,
            'ward_id': self.receiver_ward_id.id,
            'district_id': self.receiver_district_id.id,
            'city_id': self.receiver_province_id.id,
            'fee_ship': self.fee_ship,
            'cod': self.cod,
            'state': 'new',
            'num_of_package': self.no_of_package,
            'warehouse_id': self.warehouse_id.id,
            'note': self.note,
            'weight': self.weight,
            'est_deli_time': self.est_deli
        }
        return payload

    def action_booking_delivery_boys(self):
        payload = self._get_payload_delivery_boys()
        delivery_boy_id = self.env['delivery.boys'].sudo().create(payload)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Book',
            'res_model': 'delivery.boys',
            'view_mode': 'form',
            'res_id': delivery_boy_id.id,
            'target': 'current',
        }