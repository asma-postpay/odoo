# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from urllib import request
# import typing_extensions
import requests
import hashlib
import logging
import pprint

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.estate import const


_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('postpay', "Postpay")], ondelete={'postpay': 'set default'})

    #=== COMPUTE METHODS ===#

    @api.depends('code')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.

        :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda p: p.code == 'postpay').show_credentials_page = False

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
