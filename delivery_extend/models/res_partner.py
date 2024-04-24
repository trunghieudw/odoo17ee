import hashlib
import os

from odoo import fields, models


def nonce(length=40, prefix=""):
    rbytes = os.urandom(length)
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))


class ResPartner(models.Model):
    _inherit = 'res.partner'

    authorization = fields.Char(string='Authorization', help='Authorization of delivery carrier', tracking=True)
    partner_code = fields.Char(string='Code', tracking=True)
    type = fields.Selection(selection_add=[("webhook_service", "Webhook Service")])

    def get_access_token(self):
        self.write({'authorization': nonce()})
