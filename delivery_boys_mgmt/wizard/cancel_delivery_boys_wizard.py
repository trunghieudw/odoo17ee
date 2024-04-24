from odoo import fields, models, api


class CancelDeliveryBoysWizard(models.TransientModel):
    _name = 'cancel.delivery.boys.wizard'
    _description = 'This model used to cancel delivey boys order.'

    @api.model
    def default_get(self, fields_list):
        values = super(CancelDeliveryBoysWizard, self).default_get(fields_list)
        if not values.get('deli_boy_id') and 'active_model' in self._context and \
                self._context['active_model'] == 'delivery.boys':
            values['deli_boy_id'] = self._context.get('active_id')
        return values

    deli_boy_id = fields.Many2one('delivery.boys', required=True, readonly=True)
    reason = fields.Text(string='Reason', required=True)

    def action_cancel_confirm(self):
        self.deli_boy_id.write({'state': 'cancel', 'cancel_reason': self.reason})
