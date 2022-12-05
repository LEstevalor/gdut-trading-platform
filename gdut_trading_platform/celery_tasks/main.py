from celery import Celery
import os

if not os.getenv('DJANGO_SETTINGS_MODULE'):
 os.environ['DJANGO_SETTINGS_MODULE'] = 'gdut_trading_platform.settings.dev'

# 1.创建celery实例对象（下面的名称就是起个该celery实例的别名，没什么实际意义）
celery_app = Celery('gdut_trading')

# 2.加载配置文件
celery_app.config_from_object('celery_tasks.config')

# 3.自动注册异步任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.html'])
