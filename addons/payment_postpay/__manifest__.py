# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: Postpay',
    'version': '2.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider for running instalments through Postpay",
    'depends': ['base','payment','website_sale'],
    'data': [
        'views/template.xml',
        'views/payment_postpay_templates.xml',
        'views/payment_provider_views.xml',

        'data/payment_method_data.xml',
        'data/postpay_provider_data.xml'
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'payment_postpay/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
}
