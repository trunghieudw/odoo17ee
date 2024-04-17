import json

import requests
from odoo import fields, models


class ZaloAPI(models.Model):
    _name = 'zalo.api'

    name = fields.Char("Name")
    secret_key = fields.Char("Khóa bí mật")

    def sent_zns_zalo(self, record, body_required, template_data):
        company_id = self.env['res.company'].search([("id", "=", 1)])
        if body_required['phone']:
            phone_x = body_required['phone']
        if phone_x.startswith("+84"):
            phone_x = phone_x.split('+')[1]
        elif phone_x.startswith("0"):
            phone_x = phone_x[:0] + "84" + phone_x[1:len(phone_x)]
        url = "https://business.openapi.zalo.me/message/template"
        header = {
            "Content-Type": "application/json",
            # "access-token": self.env.user.company_id.zalo_token
        }
        if record.company_id.zalo_token:
            header["access-token"] = record.company_id.zalo_token
        else:
            header["access-token"] = company_id.zalo_token
        body_data = {
            "phone": phone_x,
            "template_id": body_required['template_id'],
            "template_data": template_data
        }
        data = json.dumps(body_data)
        reponse = requests.post(url, headers=header, data=data)
        data_log = {
            'type_api': "Sent ZNS Zalo",
            'phone': phone_x,
            'body_data': body_data,
            'reponse_x': reponse.json()
        }
        self.env['zalo.api.reponse'].create(data_log)


class ZaloApiRepose(models.Model):
    _name = 'zalo.api.reponse'

    type_api = fields.Char('Type Send API')
    phone = fields.Char("Phone")
    body_data = fields.Char("Body data")
    reponse_x = fields.Char("Reponse")
