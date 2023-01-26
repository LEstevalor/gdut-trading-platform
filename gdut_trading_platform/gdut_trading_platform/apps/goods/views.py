from drf_haystack.viewsets import HaystackViewSet
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView

from .models import SKU
from goods.serializers import SKUSerializer, SKUIndexSerializer


class SKUListView(ListAPIView):
    """商品列表数据查询"""
    serializer_class = SKUSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        # 若在视图中未定义get/post方法 则无法定义来接收正则出来的url路径参数, 可以利用view视图对象的 args或kwargs属性（字典取值）去获取
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id, is_launched=True)


class SKUSearchViewSet(HaystackViewSet):
    """SKU搜索"""
    index_models = [SKU]  # 指定索引模型

    serializer_class = SKUIndexSerializer
