# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""
Requrests API to magento.
"""
import json
import socket
import logging
import requests
from odoo import _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


def req(api_url, method='GET', params=None):
    """
    This method use for base on API request it call API method.
    """
    headers = {'Accept': '*/*','cache-control': 'no-cache'}
    try:
        _logger.info('Data pass to Ahamove : %s', params)
        resp = call_ssl_verify_request(method, api_url, headers, params)
        content = resp.json()
        _logger.info('API URL : %s', api_url)
        _logger.info('Response Status code : %s', resp.status_code)
    except (socket.gaierror, socket.error, socket.timeout) as err:
        raise UserError(_('A network error caused the failure of the job: %s', err))
    except Exception as err:
        raise UserError(_("Request is not Satisfied."
                          "Please check access token is correct."))
    return content

def call_ssl_verify_request(method, api_url, headers, params=None):
    if method == 'GET':
        resp = requests.get(api_url, headers=headers, params=params)
    # elif method == 'POST':
    #     resp = requests.post(api_url, headers=headers, data=json.dumps(data), verify=True, params=params)
    # elif method == 'DELETE':
    #     resp = requests.delete(api_url, headers=headers, verify=True, params=params)
    # elif method == 'PUT':
    #     resp = requests.put(api_url, headers=headers, data=json.dumps(data), verify=True, params=params)
    else:
        resp = requests.get(api_url, headers=headers, params=params)
    return resp