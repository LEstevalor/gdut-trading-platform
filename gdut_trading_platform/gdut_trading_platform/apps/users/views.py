from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenViewBase

from . import constants
from .constants import USER_ADDRESS_COUNTS_LIMIT
from .models import User, Address
from .serializers import CreateUserSerializer, MyTokenObtainPairSerializer, UserDetailSerializer, EmailSerializer, \
    UserAddressSerializer, AddressTitleSerializer


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


class AddressViewSet(UpdateModelMixin, GenericViewSet):
    """用户收获地址增删改查"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)  # is_deleted=False表示不能被逻辑删除过

    def create(self, request):
        """（增）加收获地址"""
        # 获取请求对象
        user = request.user
        count = Address.objects.filter(user=user).count()
        if count > USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '收货地址数目上限'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """处理(删)除"""
        address = self.get_object()
        address.is_deleted = True     # 逻辑删除
        address.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """（查）用户地址列表数据"""
        queryset = self.get_queryset()   # 避免一次查询出所有用户的数据集（Address.Object.All()），get_queryset提取成方法
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)   # 有带参数pk就需要detail=True
    def status(self, request, pk=None):
        """设置默认地址"""
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """修改标题"""
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
