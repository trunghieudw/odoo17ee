# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models


class TrAhamove(models.Model):
    _name = "tr.ahamove"
    _description = "Tr Ahamove"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tr_currency_id = fields.Many2one("res.currency", string='Currency', related='company_id.currency_id', readonly=True)
    tr_picking_id = fields.Many2one("stock.picking", string="Stock Picking")
    tr_fee = fields.Integer("Shipping fee", readonly=True)
    tr_address_sender = fields.Char("Address Sender", readonly=True)
    tr_address_receiver = fields.Char("Address Receiver", readonly=True)
    tr_code = fields.Char("Ahamove code")
    tr_supplier_id = fields.Char("Supplier ID", readonly=True)
    tr_supplier_name = fields.Char("Driver's name")
    shared_link = fields.Char("Share Link")
    tr_cod = fields.Char("Cod", readonly=True)
    tr_total_fee = fields.Integer("Total fee", readonly=True)
    tr_status = fields.Selection([
        ('IDLE', 'IDLE'),
        ('ASSIGNING', 'ASSIGNING'),
        ('ACCEPTED', 'ACCEPTED'),
        ('IN_PROCESS', 'IN PROCESS'),
        ('COMPLETED', 'COMPLETED'),
        ('CANCELLED', 'CANCELLED'),
        ('FAILED', 'FAILED'),
        ('BOARDED', 'BOARDED'),
        ('COMPLETING', 'COMPLETING')],
        string='Status',
        default='ASSIGNING', required=True)
    
