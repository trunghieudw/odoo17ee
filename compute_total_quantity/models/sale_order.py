from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    count_total_qty = fields.Float(string='Quantity', compute='_compute_total_product')
    count_delivered_qty = fields.Float(string='Delivered', compute='_compute_total_product')
    count_invoiced_qty = fields.Float(string='Invoiced', compute='_compute_total_product')
    count_total_product = fields.Float(string='Products', compute='_compute_total_product')
    last_modified_status_picking_note = fields.Char(string='Last Modified Status Picking Note', readonly=True,
                                                    tracking=True)

    def _compute_total_product(self):
        product_uom_qty = qty_delivered = qty_invoiced = 0
        for rec in self:
            product_ids = []
            for line in rec.order_line:
                if not line.is_delivery:
                    product_uom_qty += line.product_uom_qty
                    qty_delivered += line.qty_delivered
                    qty_invoiced += line.qty_invoiced
                    product_ids.append(line.product_id.id)
            rec.count_total_qty = product_uom_qty
            rec.count_delivered_qty = qty_delivered
            rec.count_invoiced_qty = qty_invoiced
            rec.count_total_product = len(set(product_ids))
