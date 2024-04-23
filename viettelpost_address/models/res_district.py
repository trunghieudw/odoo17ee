from odoo import fields, models, _
from odoo.exceptions import UserError

from .viettelpost_request import ViettelPostRequest


class District(models.Model):
    _name = 'res.district'
    _description = 'Districts'

    name = fields.Char('Name')
    code = fields.Char('Code')
    city_id = fields.Many2one('res.city', 'City')
    viettelpost_district_id = fields.Char()

    def action_get_wards(self):
        self.ensure_one()
        data = ViettelPostRequest('', True).get_wards(self.viettelpost_district_id)
        if data.get('error_message'):
            raise UserError(data.get('error_message'))
        wards = data.get('data', [])
        wards_dictionary = {str(d['WARDS_ID']): {'district_id': self.id, 'name': d['WARDS_NAME'], 'viettelpost_wards_id': d['WARDS_ID']} for d in wards}

        ward_ids = self.env['res.ward'].search([('district_id', '=', self.id)])
        viettelpost_ward_ids_set = ward_ids.read(['viettelpost_wards_id'])
        viettelpost_ward_ids_set = set([str(d['viettelpost_wards_id']) for d in viettelpost_ward_ids_set])

        for key, value in wards_dictionary.items():
            if key in viettelpost_ward_ids_set:
                self.env['res.ward'].browse(int(key)).write(value)
            else:
                self.env['res.ward'].create(value)

    def action_view_wards(self):
        return {'type': 'ir.actions.act_window', 'name': _('Wards'), 'res_model': 'res.ward', 'view_mode': 'tree,form', 'domain': [('district_id', '=', self.id)]}
