# -*- coding: utf-8 -*-
{
    'name': "Products and Quantity",
    'author': 'Long Duong Nhat',
    'category': 'Sales',
    'summary': """Display Total number of Products and Quantity on Sales, Picking""",
    'license': 'LGPL-3',
    'description': """""",
    'version': '17.0.1.0',
    'depends': [
        'base',
        'stock',
        'sale_management',
        'delivery'
    ],
    'data': [
        'security/res_groups.xml',
        'data/ir_config_parameter.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'report/sale_report_templates.xml',
        'report/stock_picking_report_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
