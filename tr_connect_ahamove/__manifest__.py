# -*- coding: utf-8 -*-
{
    'name': 'Connect Ahamove',
    'version': '17.0',
    'summary': 'Connect Ahamove',
    'website': '',
    'depends': [
        'base', 'stock', 'sale'
    ],
    'author': 'Truong Tran',
    'data': [
        # 'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
        'views/res_company_views.xml',
        'views/tr_ahamove_views.xml',
        'views/sale_order_views.xml',
        'security/ir.model.access.csv',
        'wizard/popup_message_views.xml',
        'wizard/popup_message_fee_views.xml',
        'wizard/popup_booking_ahamove_views.xml',
    ],
    'qweb': [
    ],
    'application': False,
    'installable': True,
}