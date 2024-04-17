{
    'name': 'E-SMS Integration',
    'version': '17.0.1.0',
    'summary': '',
    'description': """""",
    'category': 'Hidden/Tools',
    'support': 'odoo.tangerine@gmail.com',
    'author': 'Tangerine',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'sign'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/esms_api_data.xml',
        'data/esms_api_route_data.xml',
        'data/ir_config_parameter.xml',
        'data/ir_action_servers.xml',
        'wizard/esms_set_information_wizard_views.xml',
        'views/esms_api_views.xml',
        'views/esms_api_routes_views.xml',
        'views/esms_api_transaction_views.xml',
        'views/menus.xml'
    ],
    'auto_install': False,
    'application': True
}
