from odoo import fields, models, _
from odoo.exceptions import UserError

from .viettelpost_request import ViettelPostRequest


class City(models.Model):
    _inherit = 'res.city'
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    code = fields.Char('Code')
    viettelpost_province_id = fields.Char(readonly=True)

    def action_get_districts(self):
        self.ensure_one()
        data = ViettelPostRequest('', True).get_districts(self.viettelpost_province_id)
        if data.get('error_message'):
            raise UserError(data.get('error_message'))
        districts = data.get('data', [])
        districts_dictionary = {str(d['DISTRICT_ID']): {'city_id': self.id, 'name': d['DISTRICT_NAME'], 'viettelpost_district_id': d['DISTRICT_ID']} for d in districts}

        district_ids = self.env['res.district'].search([('city_id', '=', self.id)])
        viettelpost_district_ids_set = district_ids.read(['viettelpost_district_id'])
        viettelpost_district_ids_set = set([str(d['viettelpost_district_id']) for d in viettelpost_district_ids_set])

        for key, value in districts_dictionary.items():
            if key in viettelpost_district_ids_set:
                self.env['res.district'].browse(int(key)).write(value)
            else:
                self.env['res.district'].create(value)

    def action_view_districts(self):
        return {'type': 'ir.actions.act_window', 'name': _('Districts'), 'res_model': 'res.district', 'view_mode': 'tree,form', 'domain': [('city_id', '=', self.id)]}
