import os
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.conf import settings

from alipay import AliPay
from orders.models import OrderInfo
from payment.models import Payment


class PaymentView(APIView):
    """支付"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """获取支付链接"""
        # 验证订单是否有效 —— 通过订单id、用户id、支付方式、支付状态 —— 查询一下是否有，有则有效，无效抛异常
        try:
            # 使用get 和使用filter 的切片是有区别的。如果没有匹配查询的结果， get()将引发DoesNotExist 异常。
            order = OrderInfo.objects.get(order_id=order_id, user=request.user,
                                          pay_method=OrderInfo.PAY_METHODS_ENUM["ALIPAY"],
                                          status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"])
        except OrderInfo.DoesNotExist:
            # 如果是序列化器里的逻辑就丢异常，views里捕捉错误再响应
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)

        # 初始化 - 创建Alipay对象，SDK中提供的支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调 url（支付宝网站调用回来，但这里我们并没有自己的域名所以暂不需要）
            # app_private_key_string=app_private_key_string,
            # # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            # alipay_public_key_string=alipay_public_key_string,
            # 有两种写法:string 或者 path
            # 小技巧：os.path.abspath(__file__)指当前文件的绝对路径，os.path.dirname(xxx) xxx的目录，os.path.join拼接
            # 指定应用自己私钥文件的绝对路径，↓当前文件的上一级目录下keys文件夹下的app_private_key.pem文件
            # app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            app_private_key_string=open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
            # # 指定支付宝公钥文件的绝对路径
            # alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
            #                                     'keys/alipay_public_key.pem'),
            alipay_public_key_string=open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
            sign_type="RSA2",  # RSA 或者 RSA2（加密方式，后者更安全）
            debug=settings.ALIPAY_DEBUG,  # 默认 False
        )

        # 电脑支付——调用SDK的方法构造链接的参数
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,   # 订单编号
            total_amount=str(order.total_amount),  # 总价，不过注意这里要字符串，order刚好拿上面查出来的order对象
            subject="GDUT商城 %s" % order_id,  # 返回前端支付页面的标题
            return_url="http://www.gdut-trading-platform.site:8080/pay_success.html",  # 支付成功后回调的页面
            # notify_url="https://example.com/notify"  # this is optional  notify_url与前面的app_notify_url一致的
        )

        # 拼接好支付链接
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do?order_id=xxx&xxx=abc
        # 沙箱环境支付链接 :  https://openapi.alipaydev.com/gateway.do? + order_string
        # 真实环境支付链接 :  https://openapi.alipay.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 响应
        return Response({"alipay_url": alipay_url})


class PaymentStatusView(APIView):
    """验证订单状态（支付成功，修改订单状态，保存支付宝交易号）"""

    def put(self, request):
        queryDict = request.query_params   # 获取前端以查询字符串方式传入的数据（query_params不是字典，类似字典）
        data = queryDict.dict()  # 将queryDict类型转换成字典(要将中间的sign 从里面移除,然后进行验证)
        signature = data.pop("sign")  # 将sign这个数据从字典中移除

        # 创建alipay支付宝对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=open(   # 指定应用自己的私钥文件绝对路径
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem")).read(),
            alipay_public_key_string=open(   # 指定支付宝公钥文件的绝对路径
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")).read(),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 调用alipay SDK中的verify方法（PYTHON SDK的通知），验证支付结果是否是支付宝传回的
        success = alipay.verify(data, signature)  # verification
        if success:
            # 取出订单编号和支付宝交易号，绑定到一起存入数据，并且修改订单状态为已支付
            order_id = data.get('out_trade_no')
            trade_id = data.get('trade_no')

            Payment.objects.create(order_id=order_id, trade_id=trade_id)  # 因为order是ForeignKey，使用可以用order_id赋值
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['FINISHED'])
        else:
            return Response({"message": "非法请求"}, status=status.HTTP_403_FORBIDDEN)  #

        # 响应回前端
        return Response({"trade_id": trade_id})
