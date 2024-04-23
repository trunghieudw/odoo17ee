from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    viettelpost_last_status = fields.Char(string='ViettelPost latest status')
