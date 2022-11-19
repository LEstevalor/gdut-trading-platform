import logging
from random import randint
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from celery_tasks.sms.tasks import send_sms_code
from gdut_trading_platform.apps.verifications import constants

logger = logging.getLogger('django')


# Create your views here.
class SMSCodeView(APIView):
    """短信验证码（通过手机号发送并存储入数据库，有效期为5分钟）"""

    def get(self, request, mobile):
        # 1. 创建Redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 1.1 问题1-步骤1 先从Redis获取发送标记(取不到就是null，说明该手机号可以发送短信)
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return Response({'message': '手机频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 生成验证码
        sms_code = "%06d" % randint(0, 999999)
        logger.info(sms_code)

        # 3. 把验证码存储到Redis数据库
        pl = redis_conn.pipeline()
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 4. 利用云通讯发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # 触发异步任务
        send_sms_code.delay(mobile, sms_code)

        # 5. 响应
        return Response({'message': 'ok'})
