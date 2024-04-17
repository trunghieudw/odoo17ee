import json
import requests
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime
from odoo import models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import ustr


@dataclass(frozen=True)
class ESMSConnection:
    url: str
    method: str
    header: Dict[str, str]
    payload: Dict[str, Any]
    external_model: models.Model

    def execute_restful(self):
        try:
            # Because I use all requests with the method POST to call ESMS Platform so if POST else raise
            if self.method == 'post':
                res = requests.post(self.url, json=self.payload, headers=self.header, timeout=300)
            else:
                raise UserError(_('The method invalid'))
            response = res.json()
            esms_id = response.get('SMSID', False)
            esms_code = response.get('CodeResult', False)
            sms_sequence = self.payload.get('RequestId') or self.external_model._get_next_sequence_fs_gift_sms()
            self.create_esms_api_transaction(response, res.status_code, esms_id, int(esms_code), sms_sequence)
            return response
        except Exception as e:
            raise UserError(ustr(e))

    def create_esms_api_transaction(self, response, status, esms_id, esms_status, sms_sequence):
        create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = f"""
                    INSERT INTO esms_api_transaction
                    (method, url, body, response, sys_status, esms_id, esms_status, sms_sequence, create_date, create_uid) 
                    VALUES ('{self.method}', 
                            '{self.url}', 
                            '{json.dumps(self.payload)}',
                            '{json.dumps(response)}',
                            '{status}',
                            '{esms_id or ""}',
                            '{esms_status}',
                            '{sms_sequence}',
                            '{create_date}',
                            '{SUPERUSER_ID}')
                """
        query = query.replace('\n', '')
        self.external_model.env.cr.execute(query)
        self.external_model.env.cr.commit()
