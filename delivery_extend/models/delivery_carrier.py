from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    _description = 'Extend attributes for delivery carrier'

    delivery_type = fields.Selection(selection_add=[('ahamove', 'Ahamove'), ('deli_boys', 'Delivery Boys')],
                                     ondelete={'ahamove': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0}),
                                               'deli_boys': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})