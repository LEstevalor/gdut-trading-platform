from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenViewBase

from .models import User
from .serializers import CreateUserSerializer, MyTokenObtainPairSerializer, UserDetailSerializer, EmailSerializer


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


class UserDetailView(RetrieveAPIView):
    """提供⽤户详细信息"""
    # 指定序列化器
    serializer_class = UserDetailSerializer
    # 判断用户是否登录（以防之间缓存到这个页面）:⽤户身份验证：是否是登录⽤户
    permission_classes = [IsAuthenticated]
    # 重写get_object(self)，返回⽤户详情模型对象（返回前端刚刚好需要的即可）

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]   # 因为同上，也是在用户中心设置的，所以必须先判断登录与否

    def get_object(self):
        return self.request.user


class EmailVerifyView(APIView):
    """激活用户邮箱"""
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.check_verify_email_token(token)
        if not user:
            return Response({'message': '⽆效的token'}, status=status.HTTP_400_BAD_REQUEST)

        user.email_active = True
        user.save()
        return Response({'message': 'OK'})
