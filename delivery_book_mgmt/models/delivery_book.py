from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.addons.delivery_extend.wizard.booking_viettelpost_wizard import BookingViettelpostWizard
from odoo.addons.delivery_extend.wizard.booking_ahamove_wizard import BookingAhamoveWizard
from odoo.addons.delivery_extend.common.purchase import Purchase


class DeliveryBook(models.Model):
    _name = 'delivery.book'
    _inherit = ['mail.thread']
    _rec_name = 'bl_code'
    _description = 'Manage deliveries by home shipper'

    carrier_id = fields.Many2one('delivery.carrier', string='Shipping Method', required=True, tracking=True)
    carrier_type = fields.Selection(related='carrier_id.delivery_type')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # ******** private viettelpost ********
    service_type = fields.Selection(
        selection=lambda self: BookingViettelpostWizard.get_viettelpost_service_types(), string='Service Type')
    order_payment = fields.Selection(selection=lambda self: BookingViettelpostWizard.viettelpost_order_payments(),
                                     string='Order Payment')
    product_type = fields.Selection(selection=lambda self: BookingViettelpostWizard.viettelpost_product_types(),
                                    string='Product Type')
    national_type = fields.Selection(selection=lambda self: BookingViettelpostWizard.viettelpost_national_types(),
                                     string='National Type')
    store_id = fields.Many2one('viettelpost.store', string='Store')
    money_total = fields.Monetary(string='Money total', readonly=True, currency_field='currency_id')
    money_fee = fields.Monetary(string='Money fee', readonly=True, currency_field='currency_id')
    money_collection_fee = fields.Monetary(string='Money collection fee', readonly=True,
                                           currency_field='currency_id')
    money_vat = fields.Monetary(string='Money VAT', readonly=True, currency_field='currency_id')
    money_other_fee = fields.Monetary(string='Money other fee', readonly=True, currency_field='currency_id')
    # ******** private viettelpost ********

    # ******** private ahamove ********
    service_type_aha = fields.Selection(
        selection=lambda self: BookingAhamoveWizard.get_ahamove_service_types(), string='Service Type')
    payment_method_aha = fields.Selection(selection=lambda self: BookingAhamoveWizard.get_payment_method(),
                                          string='Payment Method')
    payment_aha = fields.Selection(selection=lambda self: BookingAhamoveWizard.get_payment(), string='Payment')

    merchandises_aha = fields.Selection(selection=lambda self: BookingAhamoveWizard.get_merchandises(),
                                        string='Merchandises')
    # ******** private ahamove ********

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    receiver_id = fields.Many2one('res.partner', string='Receiver', required=True)
    receiver_phone = fields.Char(string='Phone', required=True)
    receiver_street = fields.Char(string='Street', required=True)
    receiver_ward_id = fields.Many2one('res.ward', string='Ward', required_if_carrier_type='viettelpost')
    receiver_district_id = fields.Many2one('res.district', string='District', required_if_carrier_type='viettelpost')
    receiver_province_id = fields.Many2one('res.city', string='Province', required_if_carrier_type='viettelpost')

    sender_id = fields.Many2one('res.partner', string='Sender', required=True)
    sender_phone = fields.Char(string='Phone', required=True)
    sender_street = fields.Char(string='Address', required=True)
    sender_ward_id = fields.Many2one('res.ward', string='Ward', required_if_carrier_type='viettelpost')
    sender_district_id = fields.Many2one('res.district', string='District', required_if_carrier_type='viettelpost')
    sender_province_id = fields.Many2one('res.city', string='Province', required_if_carrier_type='viettelpost')

    # ******** private deli boys ********
    cus_receivable = fields.Monetary(string='Cus\'s Receivable', currency_field='currency_id')
    # ******** private deli boys ********

    deli_order_id = fields.Many2one('stock.picking', string='Delivery order', required=True, tracking=True)
    sale_id = fields.Many2one(related='deli_order_id.sale_id', string='Sale order')
    note = fields.Text(string='Note')
    num_of_package = fields.Integer(string='Number of package', tracking=True, required=True)
    fee_ship = fields.Monetary(string='Fee ship', required=True, tracking=True)
    bl_code = fields.Char(string='B/L Code', required=True, readonly=True, index=True)
    cod = fields.Monetary(string='COD', currency_field='currency_id', tracking=True)
    weight = fields.Float(string='Weight')
    state = fields.Char(string='State', required=True, tracking=True, readonly=True)
    est_deli_time = fields.Float(string='Est Delivery Time')
    tracking_link = fields.Char(string='Tracking link', required=True)
    json_create = fields.Text(string='Json Create')
    json_webhook = fields.Text(string='Json Webhook', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('carrier_id'):
            carrier_id = self.env['delivery.carrier'].browse(vals.get('carrier_id'))
            if carrier_id.delivery_type == 'ahamove':
                if not vals.get('service_type_aha'):
                    raise UserError(_('The field service type ahamove is required.'))
                elif not vals.get('payment_method_aha'):
                    raise UserError(_('The field payment method ahamove is required.'))
                elif not vals.get('payment_aha'):
                    raise UserError(_('The field payment ahamove is required.'))
                elif not vals.get('merchandises_aha'):
                    raise UserError(_('The field merchandises ahamove is required.'))
            elif carrier_id.delivery_type == 'viettelpost':
                if not vals.get('service_type'):
                    raise UserError(_('The field service type viettelpost is required.'))
                elif not vals.get('order_payment'):
                    raise UserError(_('The field order payment viettelpost is required.'))
                elif not vals.get('product_type'):
                    raise UserError(_('The field product type viettelpost is required.'))
                elif not vals.get('national_type'):
                    raise UserError(_('The field national type viettelpost is required.'))
                elif not vals.get('store_id'):
                    raise UserError(_('The field store viettelpost is required.'))
        return super(DeliveryBook, self).create(vals)

    def automated_action_complete_delivery(self, delivery_book_id: models):
        Purchase.handle_purchase_order(self.env, delivery_book_id)
