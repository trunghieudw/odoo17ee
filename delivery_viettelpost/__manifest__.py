{
    'name': 'Viettel Post Shipping',
    'summary': 'Send your shippings through Viettel Post and track them online',
    'author': 'Vmax - Erp Consulting',
    'version': '17.0.0.1',
    'license': 'OPL-1',
    'support': 'support@vmax.vn',
    'depends': ['delivery', 'viettelpost_address', 'sale'],
    'data': ['security/ir.model.access.csv', 'data/delivery_viettelpost_data.xml', 'wizard/choose_delivery_carrier_views.xml', 'views/delivery_viettelpost_views.xml', 'views/stock_picking_views.xml', 'views/sale_order_views.xml'],
    'category': 'Inventory/Delivery',
    'application': True,
}
