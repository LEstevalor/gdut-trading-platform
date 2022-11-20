from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenViewBase

from .models import User
from .serializers import CreateUserSerializer, MyTokenObtainPairSerializer


class UserView(CreateAPIView):
    """用户注册视图"""
    serializer_class = CreateUserSerializer


class UsernameCountView(APIView):
    """判断用户是否已注册"""

    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    """判断电话是否已经注册"""

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }
        return Response(data)


class MyTokenObtainPairView(TokenViewBase):
    """ jwt登录视图 按照TokenObtainPairView重写为自己调用的视图"""
    serializer_class = MyTokenObtainPairSerializer
