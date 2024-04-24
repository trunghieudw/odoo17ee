# -*- coding: utf-8 -*-
{
    'name': 'Delivery Calculate Rate',
    'author': 'Long Duong Nhat',
    'category': 'Sales',
    'summary': """Override Gate Rate Fee Ship for Sale Order""",
    'license': 'LGPL-3',
    'description': """""",
    'version': '17.0.1.0',
    'depends': [
        'base',
        'stock',
        'sale_management',
        'delivery',
        'delivery_extend'
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'data/delivery_data.xml',
        'wizard/choose_delivery_carrier_views.xml',
        'views/delivery_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
