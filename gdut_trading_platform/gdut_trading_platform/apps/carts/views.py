from django_redis import get_redis_connection
from rest_framework import response, status
from rest_framework.response import Response
from rest_framework.views import APIView
import pickle
import base64

from . import constants
from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectAllSerializer
from goods.models import SKU


class CartView(APIView):
    """购物车增删改查视图"""
    def perform_authentication(self, request):
        """重写dispatch下init的认证，直到第一次用request.user/request.auth才认证"""
        pass

    def post(self, request):
        """增"""
        # 创建序列化器做反序列化
        serializer = CartSerializer(data=request.data)
        # is_valid校验
        serializer.is_valid(raise_exception=True)
        # 获取校验后数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except:
            user = None

        # 创建响应对象
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        # 防止匿名用户is_authenticated（判断用户是否通过认证）
        if user and user.is_authenticated:
            """用户登录操作Redis记录"""
            """
            key分别为cart_xxx，selected_xxx
            hash: {'sku_id_1': 2, 'sku_id_16':1}  # 存sku_id和count
            set: {sku_id_1}                       # 存selected
            """
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()  # 创建管道
            # 添加 如果添加到sku_id在hash中已经存在,需要做增量
            # 如果要添加的sku_id在hash字典中不存在,就是新增,如果已存在,就会自动做增量计数再存储
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            # 把勾选的商品sku_id 存储到set集合中
            if selected:  # 判断当前商品是否勾选,勾选的再向set集合中添加
                pl.sadd('selected_%d' % user.id, sku_id)

            # 执行管道
            pl.execute()
            # 响应
            # return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            """用户未登录操作Cookie记录"""
            """
            {
                'sku_id_1': {'count': 1, 'selected': True},
                'sku_id_16': {'count': 1, 'selected': True}
            }
            """
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('cart')
            if cart_str:    # 说明之前cookie购物车已经有商品
                cart_str_bytes = cart_str.encode()      # 把字条串转换成bytes类型的字符串
                b64 = base64.b64decode(cart_str_bytes)  # 把bytes类型的字符串转换成bytes类型
                cart_dict = pickle.loads(b64)           # 把bytes类型转换成字典
            else:  # 如果cookie没还没有购物车数据说明是第一次来添加
                cart_dict = {}

            # 增量计数（多次增添同一个商品情况）
            if sku_id in cart_dict:    # 判断当前要添加的sku_id在字典中是否已存在
                origin_count = cart_dict[sku_id]['count']
                count += origin_count  # 原购买数据 和本次购买数据累加

            # 把新的商品添加到cart_dict字典中
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cart_dict_bytes = pickle.dumps(cart_dict)       # 将字典转换成bytes类型
            b64 = base64.b64encode(cart_dict_bytes)         # 将bytes类型转换成bytes类型的字符串
            cookie_cart_str = b64.decode()                  # bytes类型的字符串转换成字符串
            # response = Response(serializer.data, status=status.HTTP_201_CREATED) # 创建响应对象
            response.set_cookie('cart', cookie_cart_str, max_age=constants.CART_COOKIE_EXPIRES)    # 设置cookie

        return response

    def delete(self, request):
        """删"""
        # 指定序列化器，校验，获得id，判断登录态，Redis/cookie处理，Redis删hash和set，cookie字符串转字典后根据id删字典还有key再转回否删除
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']
        try:
            user = request.user
        except Exception:
            user = None
        # 创建响应对象
        response = Response(status=status.HTTP_204_NO_CONTENT)

        if user and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hdel("cart_%d" % user.id, sku_id)
            pl.srem("selected_%d" % user.id, sku_id)
            pl.execute()
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': 'cookie没有获取到'}, status=status.HTTP_400_BAD_REQUEST)

            if sku_id in cart_dict:
                del cart_dict[sku_id]
            # 如果cookie字典中还有商品则set_cookie返回，否则删除该cookie对应的key值
            if len(cart_dict.keys()):
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('cart', cart_str)
            else:
                response.delete_cookie('cart')

        return response

    def put(self, request):
        """改"""
        # 创建序列化器（序列化）
        serializer = CartSerializer(data=request.data)
        # （校验）
        serializer.is_valid(raise_exception=True)
        # （获取数据）
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        # （判断用户）
        try:
            user = request.user
        except:
            user = None
        # （创建响应对象），这里不需要响应状态码
        response = Response(serializer.data)
        if user and user.is_authenticated:
            # redis管道存储
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hset('cart_%d' % user.id, sku_id, count)  # 覆盖集合中sku_id列元素的count
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)  # 添加
            else:
                pl.srem('selected_%d' % user.id, sku_id)  # 移除
            pl.execute()
            # return Response(serializer.data)
        else:
            # 获取cookie字符串化字典取出，根据sku_id覆盖cookie数据，字典再化回cookie并set_cookie回去
            cart_str = request.COOKIES.get('cart')
            if cart_str:  # 判断cookie是否取到
                cart_str = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': '没有获取到cookie'}, status=status.HTTP_400_BAD_REQUEST)

            cart_str[sku_id] = {
                'count': count,
                'selected': selected
            }
            cart_str = base64.b64encode(pickle.dumps(cart_str)).decode()
            # response = Response(serializer.data)
            response.set_cookie('cart', cart_str)

        return response

    def get(self, request):
        """查"""
        try:
            user = request.user
        except:
            user = None
        # 有登录就查用户账户购物车的，无就看Cookie有没有数据
        if user and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)  # 字典
            selecteds = redis_conn.smembers('selected_%d' % user.id)   # 集合

            cart_dict = {}
            for sku_id_bytes, count_bytes in cart_redis_dict.items():
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(count_bytes),
                    'selected': sku_id_bytes in selecteds   # 取出集合选中的
                }

        else:
            """
            {
                1: {'count': 1, 'selected': True},
                16: {'count': 1, 'selected': True}
            }
            """
            cart_str = request.COOKIES.get('cart')
            print(cart_str)
            # 分有无数据的情况，无就返回400，有则将cookie字符串切为字典数据 才能给后面查询（目的同Redis，取ID来查询）
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_bytes)
            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)

        sku_ids = cart_dict.keys()   # 取出id开始进行查询
        skus = SKU.objects.filter(id__in=sku_ids)  # SKU模型本身是没有count和selected，而序列化器需要，因此需赋值
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        serializer = CartSKUSerializer(skus, many=True)
        # 响应
        return Response(serializer.data)


class CartSelectedAllView(APIView):
    """购物车全选"""
    def perform_authentication(self, request):
        """重写此方法延后认证"""
        pass

    def put(self, request):
        # 序列化器、校验、取数据、用户登录态、Redis/Cookie
        # Redis（选：sku_id均塞入set；不选：set清空）
        # Cookie字符串化字典，覆盖，回字符串（选：字典覆盖selected都为true；不选：清空字典值）
        serializer = CartSelectAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data["selected"]

        try:
            user = request.user
        except:
            user = None

        response = Response(serializer.data)

        if user and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            cart_dict = redis_conn.hgetall("cart_%d" % user.id)
            # 会想到用for把字典元素一个个取出来，但这里用*操作（对Redis命令的遍历操作，而下面cookie就得逐个遍历了），去keys即可
            sku_ids = cart_dict.keys()
            if selected:
                # 对应set，传列表用*；对应hash，传字典直接传输即可
                redis_conn.sadd("selected_%d" % user.id, *sku_ids)
            else:
                redis_conn.srem("selected_%d" % user.id, *sku_ids)

        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': 'cookie 没有获取到'}, status=status.HTTP_400_BAD_REQUEST)
            # 字典遍历所有
            for sku_id in cart_dict:
                cart_dict[sku_id]['selected'] = selected
            # 编码再解码
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response.set_cookie('cart', cart_str)

        return response
