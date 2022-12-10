import re
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from . import constants
from .models import User, Address
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU


class CreateUserSerializer(serializers.ModelSerializer):
    """注册序列化器"""

    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='token', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow', 'token']
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {  # 自定义校验错误信息的提示
                    'min_length': '仅允许5-20个字符的用户名',  # 比如不满足min_length的条件，则显示信息
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {  # 另外注意，修改密码的长度，不会影响对数据库存储密码时的加密操作（这里只是通过序列化器限制输入密码的长度）
                'write_only': True,  # 易漏（只做反序列化）
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的用户名',
                    'max_length': '仅允许8-20个字符的用户名',
                }
            }
        }

    def validate_mobile(self, value):
        """单独校验手机号"""
        if not re.match(r'1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式有误')
        return value

    def validate_allow(self, value):
        """是否同意协议校验"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, attrs):
        """校验两个密码是否相同 与 校验密码"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两个密码不一致')

        # 校验短信（注意前文我们定义短信的有效期为5分钟）
        redis_conn = get_redis_connection('verify_codes')
        mobile = attrs['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        # 校验码过期 或 校验码错误
        # 【特别注意】，当Redis存储数据是字符串时，取出来是bytes类型的（会导致下面的第二条件必错），需要解码（decode方法）
        if real_sms_code is None or attrs['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('请同意用户协议')

        return attrs

    def create(self, validated_data):
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        password = validated_data.pop('password')
        user = User(**validated_data)  # 创建User（下面还得存到数据库中）
        user.set_password(password)  # 密码加密后再赋值给password属性
        user.save()  # 存到数据库

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        return user


class MyTokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        # 自行添加的↓
        data['token'] = data['access']
        data['username'] = self.user.username
        data['user_id'] = self.user.id

        return data


class UserDetailSerializer(serializers.ModelSerializer):
    """⽤户详细信息序列化器"""

    class Meta:
        model = User
        # 对应前端需要返回的字段即可
        fields = ['id', 'username', 'mobile', 'email', 'email_active']


class EmailSerializer(serializers.ModelSerializer):
    """邮箱序列化器"""

    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        instance.email = validated_data['email']
        instance.save()

        # 发确认邮件到设置的邮箱（异步发送邮件）
        verify_url = instance.generate_email_verify_url()
        send_verify_email.delay(instance.email, verify_url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    """⽤户地址序列化器"""
    # 从models里的Address，直接取出其实拿到的是province的id，
    # 我们自定义的目的是为了分别拿到字符串（只用于read）和id（required=True，也就是默认表单字段不能为空）
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')   # 排除的字段

    def validate_mobile(self, value):
        """验证⼿机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('⼿机号格式错误')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return Address.objects.create(**validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title']


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """添加用户浏览历史序列化器"""
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)  # 需要放入取出的值都是（序列化、反序列化）

    def validate_sku_id(self, value):
        """检验sku_id是否存在"""
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')
        return value

    def create(self, validated_data):
        """保存"""
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        redis_conn = get_redis_connection("history")   # settings里的Redis配置
        pl = redis_conn.pipeline()   # Redis管道

        # 移除已经存在的本商品浏览记录
        pl.lrem("history_%s" % user_id, 0, sku_id)
        # 添加新的浏览记录
        pl.lpush("history_%s" % user_id, sku_id)
        # 只保存最多5条记录
        pl.ltrim("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)

        pl.execute()
        return validated_data

