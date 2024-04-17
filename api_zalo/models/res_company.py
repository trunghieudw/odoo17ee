from odoo import fields, models, api
import base64
import io
import json
from datetime import datetime
import requests
from PIL import Image
from odoo.http import request



class ResCompany(models.Model):
    _inherit = 'res.company'

    url_get_token_api_zalo = fields.Char("Url get token Zalo api", default="https://oauth.zaloapp.com/v4/oa/access_token")
    zalo_token = fields.Char("Token Zalo")
    zalo_refresh_token = fields.Char("Refresh token Zalo")
    app_id = fields.Char("ID Zalo ứng dụng")
    secret_key_zalo = fields.Char("Khóa bí mật")

    def get_token_zalo_api(self):
        company_ids = self.env['res.company'].search([])
        for company in company_ids:
            try:
                headers = {'Content-Type': 'application/x-www-form-urlencoded', 'secret_key': company.secret_key_zalo}
                request_body = {
                    "refresh_token": company.zalo_refresh_token,
                    "app_id": company.app_id,
                    "grant_type": "refresh_token"
                }
                reponse = requests.post(url=company.url_get_token_api_zalo, data=request_body, headers=headers)
                ls_json = reponse.json()
                if ls_json['access_token'] or ls_json['refresh_token']:
                    company.zalo_token = ls_json['access_token']
                    company.zalo_refresh_token = ls_json['refresh_token']
                data = {
                    'type_api': 'Get access token',
                    'body_data': request_body,
                    'reponse_x': ls_json
                }
                self.env['zalo.api.reponse'].create(data)
            except Exception as e:
                print(e)




