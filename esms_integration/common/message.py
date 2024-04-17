from enum import Enum
from odoo import _


class InvalidMessage(Enum):
    MSG_SMS_TEMPLATE_NOT_FOUND: str = _('The sms template with id: {} not found')
    MSG_API_GATEWAY_NOT_FOUND: str = _('The API Gateway {} not found')
    MSG_API_GATEWAY_NOT_ACTIVE: str = _('The API Gateway {} not active')
    MSG_API_KEY_REQUIRED: str = _('The field API Key is required')
    MSG_SECRET_KEY_REQUIRED: str = _('The field Secret Key is required')
    MSG_DOMAIN_REQUIRED: str = _('The field Domain is required')
    MSG_BRAND_NAME_REQUIRED: str = _('The field Brand Name is required')
    MSG_DATATYPE_LIST: str = _('The data type of the field {} must be List')
    MSG_DATATYPE_INT: str = _('The data type of the field {} must be Integer')
    MSG_DATATYPE_STR: str = _('The data type of the field {} must be String')
    MSG_ROUTE_NOT_FOUND: str = _('The route not found')
    MSG_ROUTE_REQUIRED: str = _('The field Route is required')
    MSG_ROUTE_METHOD_REQUIRED: str = _('The field Route Method is required')
    MSG_ROUTE_ESMS_API_REQUIRED: str = _('The Route not matching the Base API')
    MSG_ROUTE_SMS_TYPE_REQUIRED: str = _('The field SMS Type is required')
    MSG_ROUTE_NOT_ACTIVE: str = _('The route not active')
    MSG_ROUTE_HEADER_REQUIRED: str = _('The field header is required')
    MSG_LST_NUMBER_MISSING: str = _('The list phone number missing')
    MSG_CONTENT_MISSING: str = _('The content missing')
    MSG_PHONE_NUM_INVALID: str = _('The phone number: {} invalid')
    MSG_PHONE_NUM_MISSING: str = _('The phone number missing')



