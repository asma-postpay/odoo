# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from urllib import request
# import typing_extensions
import requests
import hashlib
import logging
import pprint
import base64
from werkzeug import urls
from odoo.exceptions import ValidationError, UserError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.payment_postpay import const


_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('postpay', "Postpay")], ondelete={'postpay': 'set default'})

    postpay_merchant_id = fields.Char(string="Postpay Merchant ID",

                                      groups='base.group_system')
    postpay_live_api_key = fields.Char(
        string="Live Client Key", help="The client key of the webservice user",
       )
    postpay_test_api_key = fields.Char(
        string="Test Client Key", help="The client key of the webservice user",
        )

    #=== COMPUTE METHODS ===#

    @api.depends('code')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.

        :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda p: p.code == 'postpay').show_credentials_page = True

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'postpay').update({
            'support_express_checkout': True,
            'support_manual_capture': 'partial',
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    # === CONSTRAINT METHODS ===#

    @api.constrains('state', 'code')
    def _check_provider_state(self):
        if self.filtered(lambda p: p.code == 'postpay' and p.state not in ('test', 'disabled')):
            raise UserError(_("Postpay providers should never be enabled."))

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'postpay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _postpay_get_api_url(self):
        """ Return the URL of the API corresponding to the provider's state.

        :return: The API URL.
        :rtype: str
        """
        self.ensure_one()

        environment = 'production' if self.state == 'enabled' else 'test'
        api_urls = const.API_URLS[environment]
        return api_urls.get(self.asiapay_brand, api_urls['postpay'])
    def _postpay_make_request(self, endpoint, ndpoint_param = None, data=None, method='POST'):
            """ Make a request at mollie endpoint.

            Note: self.ensure_one()

            :param str endpoint: The endpoint to be reached by the request
            :param dict data: The payload of the request
            :param str method: The HTTP method of the request
            :return The JSON-formatted content of the response
            :rtype: dict
            :raise: ValidationError if an HTTP error occurs
            """
            self.ensure_one()
            endpoint = f'/{endpoint.strip("/")}'
            url = urls.url_join(self._postpay_get_api_url(), endpoint)

           #odoo_version = service.common.exp_version()['server_version']
            module_version = self.env.ref('base.module_payment_postpay').installed_version
            merchant_id = self.postpay_merchant_id
            secret_key = self.postpay_test_api_key
            token = base64.b64encode((self.postpay_merchant_id + ':' + self.postpay_test_api_key).encode()).decode()
            _logger.info("postpay_merchant_id:\n%s", pprint.pformat(merchant_id))
            _logger.info("postpay_merchant_id:\n%s", pprint.pformat(secret_key))

            headers = {
                "Authorization": f'Basic {token}',
                "Content-Type": "application/json",
            }

            try:
                response = requests.request(method, url, json=data, headers=headers, timeout=60)
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    _logger.exception(
                        "Invalid API request at %s with data:\n%s", url, pprint.pformat(data)
                    )
                    raise ValidationError(
                        "Postpay: " + _(
                            "The communication with the API failed. Postpay gave us the following "
                            "information: %s", response.json().get('error', '')
                        ))
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                _logger.exception("Unable to reach endpoint at %s", url)
                raise ValidationError(
                    "Postpay: " + _("Could not establish the connection to the API.")
                )
            return response.json()

