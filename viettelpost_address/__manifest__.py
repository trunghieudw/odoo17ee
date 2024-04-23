{
    'name':
    'Viettel Post Shipping',
    'author':
    'Vmax - Erp Consulting',
    'version':
    '17.0.0.1',
    'license':
    'OPL-1',
    'support':
    'support@vmax.vn',
    'depends': ['base', 'base_address_extended', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        # View
        'views/res_city.xml',
        'views/res_company.xml',
        'views/res_district.xml',
        'views/res_partner.xml',
        'views/res_ward.xml',
        # Menu
        'views/contact_views.xml',
    ],
    'post_init_hook': '_install_init_data',
}
