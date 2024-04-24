from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import ustr
from odoo.exceptions import UserError
from odoo.addons.delivery_extend.common.purchase import Purchase


class CompleteDeliveryWizard(models.TransientModel):
    _name = 'complete.delivery.boys.wizard'
    _description = 'This model used confirm order delivery successfully'

    @api.model
    def default_get(self, fields_list):
        values = super(CompleteDeliveryWizard, self).default_get(fields_list)
        if not values.get('deli_boy_id') and 'active_model' in self._context and \
                self._context['active_model'] == 'delivery.boys':
            values['deli_boy_id'] = self._context.get('active_id')
        return values

    deli_boy_id = fields.Many2one('delivery.boys', string='Delivery boys order', required=True, readonly=True)
    order_image = fields.Binary('Order Image', required=True, attachment=True, help='Order confirmation Image')

    def action_done_delivery_boys(self):
        try:
            delivery_book_id = self.env['delivery.book'].sudo().search([('bl_code', '=', self.deli_boy_id.name)])
            if not delivery_book_id:
                raise UserError(f'The bl code {self.deli_boy_id.name} not found in delivery book management.')
            self.env['ir.attachment'].sudo().create({
                'name': f'{self.deli_boy_id.name}_image_complete',
                'res_id': self.deli_boy_id.id,
                'res_model': self.deli_boy_id._name,
                'datas': self.order_image,
                'public': True,
            })
            self.deli_boy_id.write({'state': 'completed'})
            delivery_book_id.write({'state': 'Giao hàng thành công'})
            Purchase.handle_purchase_order(self.env, delivery_book_id)
        except Exception as e:
            raise UserError(_(ustr(e)))
