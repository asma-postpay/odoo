# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import pprint
from werkzeug import urls
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_postpay.controllers.main import PaymentPostpayController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        _logger.info("ASMAAAAAAAAA")
        """ Override of payment to return Mollie-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'postpay':
            return res
        else:
            if isinstance(processing_values.get('currency_id'),int):
                record_currency = processing_values.get('currency_id')#self.env['res.currency'].browse(processing_values.get('currency_id'))
            else:
                record_currency = processing_values.get('currency_id')
            processing_values.update({'currency': record_currency})
            #shipping_address = self._get_shipping_address(self)
            #buyer_address = self._get_buyer_billing_address(processing_values)
            #processing_values.update(shipping_address)
            #processing_values.update(buyer_address)

        payload = self._postpay_prepare_payment_request_payload(processing_values)
        _logger.info(pprint.pformat(processing_values))
        _logger.info("sending '/payments' request for link creation:\n%s", pprint.pformat(payload))
        payment_data = self.provider_id._postpay_make_request('/checkouts', data=payload)

        # The provider reference is set now to allow fetching the payment status after redirection
        self.provider_reference = payment_data.get('id')

        # Extract the checkout URL from the payment data and add it with its query parameters to the
        # rendering values. Passing the query parameters separately is necessary to prevent them
        # from being stripped off when redirecting the user to the checkout URL, which can happen
        # when only one payment method is enabled on Mollie and query parameters are provided.
        checkout_url = payment_data['redirect_url']
        if(checkout_url):
            self.state = 'pending'
            self._set_pending()
        return {'postpay_redirect': checkout_url}

    def _postpay_prepare_payment_request_payload(self,txn_values):
        """ Create the payload for the payment request based on the transaction values.

        :return: The request payload
        'method': [const.PAYMENT_METHODS_MAPPING.get(
                self.payment_method_code, self.payment_method_code
            )],

        :rtype: dict
        """
        data = dict()
        context_dict = dict(self._context)
        data['order_id'] = txn_values.get('reference')

        data['total_amount'] = self._get_total_amount(txn_values)

        data['tax_amount'] = 10  # self._get_tamara_tax_amount(tamara_txn_values)

        data['currency'] = "AED"#self.currency_id.name

        data['shipping'] = self.get_shipping(txn_values)

        data['billing_address'] = self._get_shipping_address(txn_values)

        data['customer'] = self._get_customer_data(txn_values)

        data['items'] = self._get_items_detail(txn_values)


        data['merchant'] = self._get_mechant_url(txn_values)


        # user_lang = self.env.context.get('lang')
        # base_url = self.provider_id.get_base_url()
        # redirect_url = 'https://docs.postpay.io/v1/#workflow'#urls.url_join(base_url, MollieController._return_url)
        #
        #
        # return {
        #     'description': self.reference,
        #     'amount': {
        #         'currency': self.currency_id.name,
        #         'value': f"{self.amount:.2f}",
        #     },
        #     'confirmation_url': f'{redirect_url}',
        #     'cancellation_url': f'{redirect_url}',
        # }
        return data

    def _get_total_amount(self, txn_values):
        return self.get_decimal_value(txn_values.get('amount'))


    def get_decimal_value(self, amount):
        return round (amount * 100 , 2 )


    def get_shipping(self,txn_values):
        shipping = dict()
        shipping['id'] = txn_values['provider_id']
        shipping['name'] = "Delivery Partner"
        shipping['amount'] = self._get_shipping_amount(txn_values)
        shipping['address'] = self._get_shipping_address(txn_values)

        return shipping

    def _get_shipping_amount(self, txn_values):
        shipping_cost = self.env['sale.order'].sudo().search(
            [('name', '=', txn_values.get('reference').split('-')[0])]).amount_delivery
        return self.get_decimal_value(shipping_cost)

    def _get_shipping_address(self, txn_values):
        shipping_address = dict()
        partner_name = self.format_partner_name()
        shipping_address['first_name'] = partner_name['first_name']
        shipping_address['last_name'] = partner_name['last_name']
        shipping_address['phone'] = self.partner_phone
        shipping_address['line1'] = "Azizi Riviera"
        shipping_address['city'] = "Dubai"
        shipping_address['country'] = 'AE'

        return shipping_address

    def _get_customer_data(self, txn_values):
        customer = dict()
        partner_name = self.format_partner_name()
        customer['email'] = self.partner_email
        customer['first_name'] = partner_name['first_name']
        customer['last_name'] =  partner_name['last_name']
        customer['address'] = self._get_shipping_address(txn_values)
        return customer

    def _get_items_detail(self, txn_values):
        items_data = []
        website = self.env['website'].get_current_website()
        order = website.sale_get_order()
        for line in order.order_line:
            # if line.product_id.type not in ['service']:
           # sku_code = line.product_id.default_code if line.product_id.type == 'service' else line.product_id.default_code
            line_item = dict()
            line_item['reference'] = order.name + line.product_id.name
            line_item['description'] ="Type = " +  line.product_id.categ_id.name
            line_item['name'] = line.product_id.name
            line_item['qty'] = int(line.product_uom_qty)
            line_item['unit_price'] = self.get_decimal_value(line.price_total)
            items_data.append(line_item)
        return items_data


    def _get_mechant_url(self,txn_values):
        merchant = dict()
        reference = txn_values.get('reference')
        website_domain = self.env['sale.order'].search([('reference', '=', reference)], limit=1).website_id.domain
        base_url = website_domain or self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        merchant['confirmation_url'] = (str(urls.url_join(base_url, PaymentPostpayController.success_url)) + "?reference={}".format(reference))
        merchant['cancel_url']= str(urls.url_join(base_url, PaymentPostpayController.cancel_url)) + "?reference={}".format(reference)
        return  merchant

    def format_partner_name(self):
        customer = dict()
        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        customer['first_name'] = first_name
        customer['last_name']  = last_name
        return customer


    def _send_capture_request(self, amount_to_capture=None):
        capture_child_tx = super()._send_capture_request(amount_to_capture=amount_to_capture)
        _logger.info("provider reference from capture request response:\n%s", pprint.pformat(self.provider_reference))
        if self.provider_code != 'postpay':
            return capture_child_tx




        response_content = self.provider_id._postpay_make_request(
            endpoint='/orders/{}/capture',
            endpoint_param=self.provider_reference,
            method='POST',
        )
        _logger.info("capture request response after capture :\n%s", pprint.pformat(response_content))

        # Handle the capture request response
        status = response_content.get('status')
        formatted_amount = format_amount(self.env, amount_to_capture, self.currency_id)
        if status == 'captured':
            self._log_message_on_linked_documents(_(
                "The capture request of %(amount)s for the transaction with reference %(ref)s has "
                "been requested (%(provider_name)s).",
                amount=formatted_amount, ref=self.reference, provider_name=self.provider_id.name
            ))

        return capture_child_tx

    def _handle_notification_data(self, provider_code, notification_data):
        """ Match the transaction with the notification data, update its state and return it.

        :param str provider_code: The code of the provider handling the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction.
        :rtype: recordset of `payment.transaction`
        """
        if provider_code != 'postpay':
            _logger.info("_process_notification_data provider_code:\n%s", pprint.pformat(provider_code))
            return
        tx = self._get_tx_from_notification_data(provider_code, notification_data)
        # payment_state = notification_data.get('status')
        # if not payment_state:
        #     raise ValidationError("Postpay: " + _("Received data with missing payment state."))
        # if payment_state == 'pending':
        #     self._set_pending()
        # elif payment_state in ['APPROVED']:
        #     if not self.provider_id.capture_manually:
        #         self._send_capture_request()
        #         self._set_done()
        # else:
        #     self._set_pending()
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx


    def _process_notification_data(self, notification_data):
        _logger.info("_process_notification_data START:\n%s", pprint.pformat("asma1111"))
        _logger.info("_process_notification_data STATUS:\n%s", pprint.pformat(notification_data.get('status')))
        """ Override of payment to process the transaction based on Adyen data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)

        # Extract or assume the event code. If none is provided, the feedback data originate from a
        # direct payment request whose feedback data share the same payload as an 'AUTHORISATION'
        # webhook notification.
        status = notification_data.get('status')
        _logger.info("_process_notification_data STATUS2:\n%s", pprint.pformat(status))

        # Update the provider reference. If the event code is 'CAPTURE' or 'CANCELLATION', we
        # discard the pspReference as it is different from the original pspReference of the tx.
        if 'order_id' in notification_data and status in ['APPROVED', 'CAPTURED']:
            self.provider_reference = notification_data.get('order_id')
            _logger.info("The updated provider reference:\n%s", pprint.pformat(self.provider_reference))
        #
        # # Update the payment method.
        # payment_method_data = notification_data.get('paymentMethod', '')
        # if isinstance(payment_method_data, dict):  # Not from webhook: the data contain the PM code.
        #     payment_method_type = payment_method_data['type']
        #     if payment_method_type == 'scheme':  # card
        #         payment_method_code = payment_method_data['brand']
        #     else:
        #         payment_method_code = payment_method_type
        # else:  # Sent from the webhook: the PM code is directly received as a string.
        #     payment_method_code = payment_method_data
        #
        # payment_method = self.env['payment.method']._get_from_code(
        #     payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        # )
        # self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_state = notification_data.get('status')
        _logger.info("_process_notification_data provider_reference:\n%s", pprint.pformat(payment_state))
        if not payment_state:
            raise ValidationError("Postpay: " + _("Received data with missing payment state."))
        if payment_state == 'pending':
            self._set_pending()
        elif payment_state in ['APPROVED']:
            if not self.provider_id.capture_manually:
                self._send_capture_request()
                self._set_done()
        else:
            self._set_pending()




