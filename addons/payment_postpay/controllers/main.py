
import json
import pprint
import werkzeug
import logging
import requests
from odoo import  _, http
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

# try:
#     import jwt
# except Exception as e:
#     _logger.error("Python's jwt Library is not installed.")

APIEND = {
        "test_url": "https://api-sandbox.tamara.co",
        "live_url": "https://api.tamara.co",
    }


class PaymentPostpayController(http.Controller):
    success_url = '/payment/postpay/success'
    cancel_url = '/payment/postpay/cancel'

    @http.route([success_url, cancel_url], type='http', auth='public', csrf=False)
    def payment_checkout_postpay_return(self, *args, **kwargs):
        _logger.info(
            'Postpay: Entering form_feedback with post data %s', pprint.pformat(kwargs))
        request.env['payment.transaction'].sudo()._handle_notification_data('postpay',kwargs)

        return werkzeug.utils.redirect('/payment/status')

