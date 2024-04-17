import json
import re
import logging
import base64
from typing import List, NoReturn
from odoo import models, fields, _, modules, tools, api
from odoo.tools import ustr
from odoo.exceptions import UserError
from odoo.addons.esms_integration.common.message import InvalidMessage
from odoo.addons.esms_integration.api.esms_connection import ESMSConnection
_logger = logging.getLogger(__name__)


SANDBOX_ENV_TEST: int = 1


class EsmsAPI(models.Model):
    _name = 'esms.api'
    _inherit = ['mail.thread']
    _description = 'This module is used to save account configuration information and API E-SMS'

    @api.depends('icon')
    def get_icon_image(self):
        for instance in self:
            instance.icon_image = ''
            if instance.icon:
                path_parts = instance.icon.split('/')
                path = modules.get_module_resource(path_parts[1], *path_parts[2:])
            else:
                path = modules.module.get_module_icon(instance.name)
            if path:
                with tools.file_open(path, 'rb') as image_file:
                    instance.icon_image = base64.b64encode(image_file.read())

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, readonly=True)
    domain = fields.Char(string='Domain', required=True)
    icon = fields.Char(string='Icon')
    icon_image = fields.Binary(string='Icon image', compute='get_icon_image')
    active = fields.Boolean(default=True)
    summary = fields.Text(string='Summary')
    route_ids = fields.One2many(comodel_name='esms.api.routes', inverse_name='esms_api_id')
    api_key = fields.Char(string='API Key', required=True, readonly=True)
    secret_key = fields.Char(string='Secret Key', required=True, readonly=True)
    brand_name = fields.Char(string='Brand Name', required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    balance = fields.Monetary(string='Balance', currency_field='currency_id')
    website = fields.Char(string='Website', required=True, readonly=True)
    env_current = fields.Char(compute='_get_param_esms_env')

    def _get_param_esms_env(self):
        for rec in self:
            rec.env_current = self.env['ir.config_parameter'].sudo().get_param('sandbox_esms', SANDBOX_ENV_TEST)

    def change_environment(self) -> NoReturn:
        """
            0: E-SMS Production environment
            1: E-SMS Staging environment
        """
        env_esms = self._context.get('env_esms', SANDBOX_ENV_TEST)
        self.env['ir.config_parameter'].sudo().set_param('sandbox_esms', env_esms)

    @api.model
    def _get_balance(self, esms_api_id: models.Model):
        route_id = self._get_esms_route('get_balance')
        url = esms_api_id.domain + route_id.route
        payload = {
            'ApiKey': esms_api_id.api_key,
            'SecretKey': esms_api_id.secret_key,
        }
        client = ESMSConnection(url, route_id.method, json.loads(route_id.header), payload, self)
        response = client.execute_restful()
        esms_api_id.sudo().write({'balance': response.get('Balance', 0)})

    @staticmethod
    def _validate_esms_api(esms_api_id) -> NoReturn:
        if not esms_api_id:
            raise UserError(InvalidMessage.MSG_API_GATEWAY_NOT_FOUND.value.format('E-SMS'))
        elif not esms_api_id.active:
            raise UserError(InvalidMessage.MSG_API_GATEWAY_NOT_ACTIVE.value.format('E-SMS'))
        elif not esms_api_id.api_key:
            raise UserError(InvalidMessage.MSG_API_KEY_REQUIRED.value)
        elif not esms_api_id.secret_key:
            raise UserError(InvalidMessage.MSG_SECRET_KEY_REQUIRED.value)
        elif not esms_api_id.domain:
            raise UserError(InvalidMessage.MSG_DOMAIN_REQUIRED.value)
        elif not esms_api_id.brand_name:
            raise UserError(InvalidMessage.MSG_BRAND_NAME_REQUIRED.value)

    def _get_esms_api(self) -> models.Model:
        esms_api_id = self.env['esms.api'].search([('code', '=', 'esms_api')], limit=1)
        self._validate_esms_api(esms_api_id)
        return esms_api_id

    @staticmethod
    def _validate_route_esms(route_id: models.Model) -> NoReturn:
        if not route_id:
            raise UserError(InvalidMessage.MSG_ROUTE_NOT_FOUND.value)
        elif not route_id.route:
            raise UserError(InvalidMessage.MSG_ROUTE_REQUIRED.value)
        elif not route_id.method:
            raise UserError(InvalidMessage.MSG_ROUTE_METHOD_REQUIRED.value)
        elif not route_id.esms_api_id:
            raise UserError(InvalidMessage.MSG_ROUTE_ESMS_API_REQUIRED.value)
        elif not route_id.sms_type:
            raise UserError(InvalidMessage.MSG_ROUTE_SMS_TYPE_REQUIRED.value)
        elif not route_id.active:
            raise UserError(InvalidMessage.MSG_ROUTE_NOT_ACTIVE.value)
        elif not route_id.header:
            raise UserError(InvalidMessage.MSG_ROUTE_HEADER_REQUIRED.value)

    def _get_esms_route(self, route: str) -> models.Model:
        route_id = self.env['esms.api.routes'].search([('code', '=', route)], limit=1)
        self._validate_route_esms(route_id)
        return route_id

    def _get_sandbox_esms(self):
        sandbox = self.env['ir.config_parameter'].sudo().get_param('sandbox_esms', SANDBOX_ENV_TEST)
        return int(sandbox)

    @staticmethod
    def _validate_datatype_parameter(phone_numbers: List[str], content: str, route_code: str) -> NoReturn:
        if not isinstance(phone_numbers, List):
            raise UserError(InvalidMessage.MSG_DATATYPE_LIST.value.format('phone_numbers'))
        elif not isinstance(content, str):
            raise UserError(InvalidMessage.MSG_DATATYPE_STR.value.format('sms_template_id'))
        elif not isinstance(route_code, str):
            raise UserError(InvalidMessage.MSG_DATATYPE_STR.value.format('route'))
        elif not phone_numbers:
            raise UserError(InvalidMessage.MSG_LST_NUMBER_MISSING.value)
        elif not content:
            raise UserError(InvalidMessage.MSG_CONTENT_MISSING.value)

    def _get_next_sequence_fs_gift_sms(self) -> str:
        sequence_id = self.env.ref('esms_integration.seq_fs_gift_sms_sequence')
        next_document = sequence_id.get_next_char(sequence_id.number_next_actual)
        self._cr.execute("""
                            SELECT sms_sequence 
                            FROM esms_api_transaction
                            WHERE sms_sequence ilike '{prefix}%';
                        """.format(prefix=sequence_id.prefix))
        query_res = self._cr.fetchall()
        while next_document in [res[0] for res in query_res]:
            next_tmp = self.env['ir.sequence'].next_by_code(sequence_id.code)
            next_document = next_tmp
        return next_document

    @staticmethod
    def _validate_phone_number(phone_number: str) -> bool:
        """
            :param phone_number: This is a phone number need validate
            Valid phone number:
                - Start with prefix: 03, 05, 07, 08, 09, 84, +84
                - Number length is 10 with prefix: 03, 05, 07, 08, 09
                - Number length is 11 with prefix: 84, +84
            :return boolean: Phone number valid or invalid
        """
        pattern = r"([\+84|84|0]+(3|5|7|8|9))+([0-9]{8})\b"
        return bool(re.match(pattern, phone_number))

    def _send_esms(self, phone_numbers: List[str], content: str, route: str):
        """
            Summary: This is a function used to send e-sms
            :param phone_numbers: This is a list number of phones that want to send sms
            :param content: This is a message that want to send for receiver
            :param route: This is the code of the e-sms API route
        """
        self._validate_datatype_parameter(phone_numbers, content, route)
        esms_sandbox = self._get_sandbox_esms()
        route_id = self._get_esms_route(route)
        esms_api_id = self._get_esms_api()
        for phone_number in phone_numbers:
            if not phone_number:
                _logger.info(InvalidMessage.MSG_PHONE_NUM_MISSING.value)
                continue
            elif not self._validate_phone_number(phone_number):
                _logger.info(InvalidMessage.MSG_PHONE_NUM_INVALID.value.format(phone_number))
                continue
            odoo_sms_sequence = self._get_next_sequence_fs_gift_sms()
            payload = {
                'ApiKey': esms_api_id.api_key,
                'SecretKey': esms_api_id.secret_key,
                'Brandname': esms_api_id.brand_name,
                'Phone': phone_number,
                'Content': content,
                'Sandbox': esms_sandbox,
                'Unicode': 0,  # 0: Gửi không dấu
                'SmsType': route_id.sms_type,
                'RequestId': odoo_sms_sequence
            }
            if route_id.is_unicode:
                payload.update({'Unicode': 1})  # 1: Gửi có dấu
            try:
                _logger.info(f'\nStart send sms:\nNumber phone: {phone_number}\nContent: {content}')
                url = esms_api_id.domain + route_id.route
                client = ESMSConnection(url, route_id.method, json.loads(route_id.header), payload, self)
                client.execute_restful()
                self._get_balance(esms_api_id)
                _logger.info(f'\nSend sms successfully:\nNumber phone: {phone_number}\nContent: {content}')
            except Exception as e:
                _logger.exception(f'\nSend sms error:\nNumber phone: {phone_number}\nContent: {content}\n{ustr(e)}')


class EsmsAPIRoute(models.Model):
    _name = 'esms.api.routes'
    _inherit = ['mail.thread']
    _description = 'This module is used to store the routes of the E-SMS API'

    esms_api_id = fields.Many2one(comodel_name='esms.api', string='Base API', required=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    route = fields.Char(string='Route', required=True)
    header = fields.Char(string='Header', required=True)
    method = fields.Selection([
        ('post', 'POST'),
        ('get', 'GET'),
        ('put', 'PUT'),
        ('delete', 'DELETE')
    ], string='Method', required=True)
    active = fields.Boolean(default=True)
    # is_unicode - Gửi nội dung có dấu:
    # 1: Có dấu
    # 0: Không dấu
    # Mặc định gửi không dấu -> True: Có dấu
    is_unicode = fields.Boolean(string='Is Unicode', default=False)
    sms_type = fields.Selection([
        ('not_use', 'Not Use'),
        ('1', 'SMS Type 1 - Gửi tin quảng cáo'),
        ('2', 'SMS Type 2 - Chăm sóc khách hàng'),
        ('8', 'SMS Type 8 - Cố định giá rẻ')
    ], required=True, string='SMS Type')


class EsmsAPITransaction(models.Model):
    _name = 'esms.api.transaction'
    _order = 'sms_sequence desc'
    _rec_name = 'esms_id'
    _description = 'This module is used to save call API E-SMS transactions'

    sms_sequence = fields.Char(string='Sequence', required=True)
    sys_status = fields.Char(string='System Status', required=True)
    url = fields.Char(string='URL', required=True)
    body = fields.Char(string='Body', required=True)
    response = fields.Char(string='Response', required=True)
    method = fields.Selection([
        ('post', 'POST'),
        ('get', 'GET'),
        ('put', 'PUT'),
        ('delete', 'DELETE')
    ], string='Method', required=True)
    esms_id = fields.Char(string='E-SMS-ID', required=True)
    esms_status = fields.Char(string='E-SMS Status', required=True)
