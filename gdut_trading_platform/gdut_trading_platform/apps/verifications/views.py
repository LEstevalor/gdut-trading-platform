from django.shortcuts import render
from rest_framework.views import APIView


# Create your views here.
class SMSCodeView(APIView):
    """短信验证码"""

    def get(self, request, mobile):
        # 1. 生成验证码
        # 2. 创建Redis连接对象
        # 3. 把验证码存储到Redis数据库
        # 4. 利用。。。发送短信验证码
        # 5. 响应
        pass
