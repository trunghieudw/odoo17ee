from odoo import fields, models, _, api
from odoo.exceptions import UserError

class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'
    _description = 'Delivery Carrier Selection Wizard'

    ahamove_service = fields.Selection([
        ('SGN-BIKE', 'Sai Gon Bike'),
        ('SGN-SAMEDAY', 'Ahamove 4H SGN'),
        ('HAN-BIKE', 'Ha Noi Bike'),
        ('VCA-BIKE', 'Can Tho Bike'),
        ('DAD-BIKE', 'Da Nang Bike'),
        ('SGN-VAN-1000', 'Sai Gon VAN1000'),
        ('HAN-VAN-1000', 'Ha Noi VAN1000')],
        default='SGN-BIKE')

    @api.onchange('order_id')
    def _onchange_order_id(self):
        # fixed and base_on_rule delivery price will computed on each carrier change so no need to recompute here
        if self.carrier_id and self.order_id.delivery_set \
                and self.delivery_type not in ('fixed', 'base_on_rule', 'viettelpost', 'google_map', 'ahamove'):
            vals = self._get_shipment_rate()
            if vals.get('error_message'):
                warning = {
                    'title': '%s Error' % self.carrier_id.name,
                    'message': vals.get('error_message'),
                    'type': 'notification',
                }
                return {'warning': warning}

    def update_price(self):
        context = dict(self.env.context)
        if self.carrier_id.delivery_type == 'ahamove' and not self.ahamove_service:
            raise UserError(_('The field Ahamove Service is required.'))
        context.update({'ahamove_service': self.ahamove_service})
        return super(ChooseDeliveryCarrier, self.with_context(context)).update_price()
