from odoo import fields, models, api


class ESMSSetInformationWizard(models.TransientModel):
    _name = 'esms.set.information.wizard'
    _description = 'This module used to set API Key and Secret Key for authentication E-SMS API'

    @api.model
    def default_get(self, fields_list):
        values = super(ESMSSetInformationWizard, self).default_get(fields_list)
        if not values.get('esms_api_id') and 'active_model' in self._context \
                and self._context['active_model'] == 'esms.api':
            values['esms_api_id'] = self._context.get('active_id')
        return values

    esms_api_id = fields.Many2one(comodel_name='esms.api')
    secret_key = fields.Char(string='Secret Key', required=True)
    api_key = fields.Char(string='API Key', required=True)
    brand_name = fields.Char(string='Brand Name', required=True)

    def action_esms_set_api_key(self):
        self.esms_api_id.write({
            'secret_key': self.secret_key,
            'api_key': self.api_key,
            'brand_name': self.brand_name
        })
