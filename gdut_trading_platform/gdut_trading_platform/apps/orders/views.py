from decimal import Decimal
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from goods.models import SKU
from orders.serializers import OrderSettlementSerializer, CommitOrderSerializer


class OrderSettlementView(APIView):
    """订单结算"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取订单信息"""
        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)

        # 把hash中的勾选商品的sku_id和对应的count保存在cart里
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        # 再通过cart查出对应商品的信息，把count存到该字典skus中
        # count是前端需要的，而且随时变动，并不需要存数据库，序列化器有就够了，所以SKU并无该字段，传到到前端
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]

        # 运费（其实这里应该按不同地区位置变动计算，但我们这里避免复杂计算，暂做默认设置）
        freight = Decimal('10.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)


class CommitOrderView(CreateAPIView):
    """ 保存订单 """
    serializer_class = CommitOrderSerializer

    # 指定权限
    permission_classes = [IsAuthenticated]
