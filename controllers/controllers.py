# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, redirect_with_hash
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Alipay(http.Controller):

    _return_url = "/payment/alipay/validate"

    @http.route('/payment_alipay/jump', auth='public')
    def index(self, **kw):
        """跳转至支付宝付款页面"""
        kw["csrf_token"] = request.csrf_token()
        alipay = request.env["payment.acquirer"].sudo().search(
            [('provider', '=', 'alipay')], limit=1)
        return redirect_with_hash(alipay._get_alipay_url(kw))

    def validate_pay_data(self, **kwargs):
        """验证支付结果"""
        """
        {
            'charset': 'utf-8', 
            '   ': 'SO824-6', 
            'method': 'alipay.trade.page.pay.return', 
            'total_amount': '1.00', 
            'sign': 'kMKtZpyVMZT+GJIZVXL2ASdc7uy0uxa6iJVElKpa3a+YRROOyGDOxQX4wjC4xvPXre9rEuwygm83mu5LYQRyYQnlsZEz1UHhrQvnKpxjzbDZxDTzr32T2d2rpZYKllSfmB8FmVHGp57vCq7XiVnRyySeruoPxfnwB/eelT1RKRO0yu5T7Hr9M9W8w/av9l07w96er8CJiG3T4LKi91G8YvNRXUqU9WmscpZj2OuUGnaqDV9hp3drAMkUtV/w/vI3hJi72oqXzJF6V3a0ElFQ87UUVUtQ0xjfGoXUcVMD7YE1Ms5F5Qj0+81JJVt1cIl1yrbhqWR7axaYJ/NInrFBkA==', 
            'trade_no': '2019110522001414381000118540', 
            'auth_app_id': '2016101100664659', 
            'version': '1.0', 
            'app_id': '2016101100664659', 
            'sign_type': 'RSA2', 
            'seller_id': '2088102179155775', 
            'timestamp': '2019-11-05 16:26:20'
        }
        """
        res = request.env['payment.transaction'].sudo(
        ).form_feedback(kwargs, 'alipay')
        return res

    @http.route('/payment/alipay/validate', type="http", auth="none", methods=['POST', 'GET'], csrf=False)
    def alipay_validate(self, **kwargs):
        """验证支付结果"""
        _logger.info("开始验证支付宝支付结果...")
        try:
            res = self.validate_pay_data(**kwargs)
        except ValidationError:
            _logger.exception("支付验证失败")
        return redirect_with_hash("/payment/process")

    @http.route('/payment/alipay/notify', type="http", auth='none', method=["POST"])
    def alipay_notify(self, **kwargs):
        """接收支付宝异步通知"""
        _logger.debug(f"接收支付宝异步通知...收到的数据:{kwargs}")
        pass
