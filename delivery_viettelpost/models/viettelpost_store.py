from odoo import fields, models


class ViettelPostStore(models.Model):
    _name = 'viettelpost.store'
    _description = 'Viettel Post Store'

    name = fields.Char('name')
    phone = fields.Char('phone')
    address = fields.Char('address')
    group_address_id = fields.Char('Group Address ID')
    customer_id = fields.Char('Customer ID')
