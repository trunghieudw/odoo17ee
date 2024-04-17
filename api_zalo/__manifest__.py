{
    'name': 'Api Zalo',
    'version': '1.0',
    'summary': 'API ZALO',
    'author': 'Swann',
    'website': 'Website',
    'depends': ['base', 'contacts', 'sale', 'stock', 'mrp', 'contacts'],
    'data': [
        'views/message_zalo_view.xml',
        # 'views/templates.xml',
        'views/res_partner_view_inherit.xml',
        'views/zalo_api_view.xml',
        'views/res_company.xml',
        'views/menu.xml',
        'security/ir.model.access.csv',
        # 'data/zalo_notify_template.xml',
        'data/cronjob_get_token_api_zalo.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
