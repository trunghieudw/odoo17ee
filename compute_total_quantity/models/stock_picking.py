# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    last_modified_status_date = fields.Datetime(string='Last Modified Status Date', tracking=True)
    count_total_product = fields.Float(string='Products', compute='_compute_total_quantity')
    count_total_demand = fields.Float(string='Demand', compute='_compute_total_quantity')
    count_total_reserved = fields.Float(string='Reserved', compute='_compute_total_quantity')
    count_total_done = fields.Float(string='Done', compute='_compute_total_quantity')

    def _compute_total_quantity(self):
        demand_qty = reserved_qty = done_qty = 0
        for rec in self:
            product_ids = []
            for line in rec.move_ids_without_package:
                demand_qty += line.product_uom_qty
                reserved_qty += line.forecast_availability
                done_qty += line.quantity_done
                product_ids.append(line.product_id.id)
            rec.count_total_demand = demand_qty
            rec.count_total_reserved = reserved_qty
            rec.count_total_done = done_qty
            rec.count_total_product = len(set(product_ids))

    def _update_last_modified_status_date_and_note(self):
        note = self.env['ir.config_parameter'].sudo().get_param('last_modified_status_picking_note')
        for rec in self:
            rec.last_modified_status_date = datetime.now()
            time = rec.last_modified_status_date + timedelta(hours=7)
            rec.sale_id.write({
                'last_modified_status_picking_note': note.format(picking=rec.name,
                                                                 state=dict(rec._fields['state'].selection).get(rec.state),
                                                                 datetime=time.strftime("%m/%d/%Y %H:%M:%S"))
            })

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        if res is not True:
            return res
        self._update_last_modified_status_date_and_note()
        return res

    def sh_cancel(self):
        res = super(StockPicking, self).sh_cancel()
        self._update_last_modified_status_date_and_note()
        return res

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if res is not True:
            return res
        self._update_last_modified_status_date_and_note()
        return res

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self._update_last_modified_status_date_and_note()
        return res

    def do_unreserve(self):
        res = super(StockPicking, self).do_unreserve()
        if res is not True:
            return res
        self._update_last_modified_status_date_and_note()
        return res
