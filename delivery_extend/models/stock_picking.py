from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    deli_book_id = fields.Many2one('delivery.book', string='Delivery Book')

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if res is not True:
            return res
        total_package = self.env.context.get('total_package', 0)
        self.write({'x_studio_total_package': total_package})
        return res

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