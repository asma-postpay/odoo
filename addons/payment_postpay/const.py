# Part of Odoo. See LICENSE file for full copyright and licensing details.

# The codes of the payment methods to activate when Demo is activated.
DEFAULT_PAYMENT_METHOD_CODES = [
    'postpay',
]

API_URLS = {
    'production': {
        'postpay': 'https://api.postpay.io',
    },
    'test': {
        'postpay': 'https://sandbox.postpay.io',
    }
}
