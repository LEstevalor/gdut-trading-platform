import logging
from random import randint
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from gdut_trading_platform.apps.verifications import constants
from gdut_trading_platform.libs.yuntongxun.sms import CCP

logger = logging.getLogger('django')


# Create your views here.
class SMSCodeView(APIView):
    """短信验证码"""

    # （问题1）为解决60s内一个手机号只能发送一个验证码的问题
    # （问题2）解决Redis连接多（存储时每次操作都连接，消耗性能），管道一次性做处理
    def get(self, request, mobile):
        # 1. 创建Redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 1.1 问题1-步骤1 先从Redis获取发送标记(取不到就是null，说明该手机号可以发送短信)
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return Response({'message': '手机频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)
            # 这里是根据前端400写的（发送短信错误提示）

        # 2. 生成验证码
        sms_code = "%06d" % randint(0, 999999)
        logger.info(sms_code)
        # 3. 把验证码存储到Redis数据库
        # （问题2-步骤1）创建Redis管道
        pl = redis_conn.pipeline()
        # （问题2-步骤2）把原先Redis的直接setex改为加入管道中
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 3.1 （问题1-步骤2）存储一个标记，表示此手机号已发送过短信  标记有效期为60s (最后传一个整数即可，无所谓，一般写1)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # （问题2-步骤3）执行管道
        pl.execute()

        # 4. 利用云通讯发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # 5. 响应
        return Response({'message': 'ok'})
