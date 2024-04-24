{
    'name': 'Delivery Extend',
    'version': '17.0.1.0',
    'summary': 'This module is used for open wizard handle assign delivery carrier',
    'description': """""",
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'author': 'Tangerine',
    'license': 'LGPL-3',
    'depends': ['mail', 'tr_connect_ahamove', 'delivery_viettelpost'],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_carrier_data.xml',
        'data/res_partner_data.xml',
        'data/ir_config_parameter.xml',
        'wizard/select_deli_carrier_wizard_views.xml',
        'wizard/booking_viettelpost_wizard_views.xml',
        'wizard/booking_ahamove_wizard_views.xml',
        'wizard/booking_delivery_boys_wizard_views.xml',
        'wizard/put_in_pack_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'views/menus.xml'
    ],
    'application': True
}