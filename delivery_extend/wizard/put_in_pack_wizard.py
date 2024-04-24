from odoo import fields, models, _
from odoo.exceptions import UserError


class PutInPackWizard(models.TransientModel):
    _name = 'put.in.pack.wizard'

    def default_get(self, fields_list):
        values = super(PutInPackWizard, self).default_get(fields_list)
        if not values.get('transfer_id') and 'active_model' in self._context and \
                self._context['active_model'] == 'stock.picking':
            values['transfer_id'] = self._context.get('active_id')
        return values

    transfer_id = fields.Many2one('stock.picking', string='Transfer', required=True, readonly=True)
    total_package = fields.Integer(string='Total Packing')

    def button_validate(self):
        if self.total_package < 1:
            raise UserError(_('The value of field total packing must be bigger 0.'))
        res = self.transfer_id.button_validate()
        if res is not True:
            context = dict(res['context'])
            context.update({'total_package': self.total_package})
            res['context'] = context
            return res
        self.sudo().transfer_id.write({'x_studio_total_package': self.total_package})
        return res
