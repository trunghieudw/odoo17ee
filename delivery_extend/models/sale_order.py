from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deli_book_id = fields.Many2one('delivery.book', string='Delivery Book')

    def action_view_delivery_book(self):
        if not self.deli_book_id:
            raise UserError(_('Delivery book not found.'))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Book',
            'res_model': 'delivery.book',
            'view_mode': 'form',
            'res_id': self.deli_book_id.id,
            'target': 'current',
        }
