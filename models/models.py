# -*- coding: utf-8 -*-

from odoo import models, fields, api
from alipay.api import AliPay
from Crypto.PublicKey import RSA
import base64
from urllib.parse import quote_plus
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AcquirerAlipay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('alipay', "AliPay")])
    alipay_appid = fields.Char("Alipay AppId")
    alipay_secret = fields.Binary("Alipay Private Key")
    alipay_sign_type = fields.Selection(
        selection=[('rsa', 'RSA'), ('rsa2', 'RSA2')], string="Sign Type")

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(AcquirerAlipay, self)._get_feature_support()
        res['fees'].append('alipay')
        return res

    @api.model
    def _get_alipay_url(self, params=None):
        """Alipay URL"""
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        params["return_url"] = f'{base_url}{params["return_url"]}'
        params["notify_url"] = f'{base_url}{params["notify_url"]}'
        # 额外的参数
        passback_params = quote_plus("&".join(
            f"{k}={v}" for k, v in params.items() if v)) if params else None
        private_key = RSA.importKey(base64.b64decode(
            self.alipay_secret).decode('utf-8'))
        if self.environment == "prod":
            alipay = AliPay(self.alipay_appid, private_key,
                            sign_type=self.alipay_sign_type,
                            return_url=params["return_url"],
                            notify_url=params["notify_url"])
        else:
            alipay = AliPay(self.alipay_appid,
                            private_key,
                            return_url=params["return_url"],
                            notify_url=params["notify_url"],
                            sign_type=self.alipay_sign_type, sandbox=True)

        return alipay.pay.trade_page_pay(params["reference"], params["amount"],
                                         params["reference"], product_code="FAST_INSTANT_TRADE_PAY",
                                         passback_params=passback_params)

    @api.multi
    def alipay_get_form_action_url(self):
        return "/payment_alipay/jump"

    @api.multi
    def alipay_form_generate_values(self, values):
        # base_url = self.env['ir.config_parameter'].sudo(
        # ).get_param('web.base.url')
        alipay_tx_values = dict(values)
        alipay_tx_values.update({
            "return_url": "/payment/alipay/validate",
            "notify_url": "/payment/alipay/notify"
        })
        return alipay_tx_values


class TxAlipay(models.Model):
    _inherit = 'payment.transaction'

    alipay_txn_type = fields.Char('Transaction type')

    @api.model
    def _alipay_form_get_tx_from_data(self, data):
        """获取支付事务"""
        if not data.get("out_trade_no", None):
            raise ValidationError("订单号错误")
        reference = data.get("out_trade_no")
        txs = self.env["payment.transaction"].search(
            [('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'Alipay: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    @api.multi
    def _alipay_form_validate(self, data):
        """验证支付"""
        print('*********')
        print(data)
        res = {
            "acquirer_reference": ""
        }
        # [FIXME]验证具体逻辑
        self._set_transaction_done()
        return self.write(res)
