from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from goods.models import SKU
from goods.search_indexes import SKUIndex


class SKUSerializer(serializers.ModelSerializer):
    """sku商品序列化器"""
    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']
        # 显然对于SKU的所有字段['id', 'name', 'caption', 'goods', 'category', 'price',
        # 'cost_price' , 'market_price', 'stock', 'sales', 'comments', 'is_launched', 'default_image_url'
        # 我们页面并不是都需要的，这里只指定我们需要的五个字段，当然注意到我们这里继承的（看前端页面或设计方案就知道了）


class SKUIndexSerializer(HaystackSerializer):
    """SKU索引结果数据序列化器"""
    object = SKUSerializer(read_only=True)

    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'object')
