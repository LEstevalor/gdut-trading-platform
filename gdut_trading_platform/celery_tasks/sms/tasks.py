# 编辑异步任务代码
from celery_tasks.sms import constants
from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.main import celery_app


@celery_app.task(name='send_sms_code')   # 使用装饰器注册任务
def send_sms_code(mobile, sms_code):
    """
    发送短信的celery异步任务
    :param mobile: 手机号
    :param sms_code: 验证码
    """
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
