{
    'name': "estate",
    'license': 'OPL-1',
    'version': '1.0',
    'sequence': 1,
    'depends': ['base' , 'payment','website_sale'],
    'author': "Asma",
    'category': 'sales',
    'description': """
    Description text
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/payment_postpay_templates.xml',
        'views/template.xml',
        'data/payment_method_data.xml',
        'data/postpay_provider_data.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
