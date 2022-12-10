from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    """购物车序列化器"""
    sku_id = serializers.IntegerField(label="商品ID", min_value=1)
    count = serializers.IntegerField(label="购物数量")
    selected = serializers.BooleanField(default=True, label="商品勾选状态")

    def validated_sku_id(self, value):
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("sku_id不存在")

        return value


class CartSKUSerializer(serializers.ModelSerializer):
    """购物车商品数据序列化器"""
    count = serializers.IntegerField(label='数量')
    selected = serializers.BooleanField(label='是否勾选')

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')   # 前端页面需要展示所用到的数据


class CartDeleteSerializer(serializers.Serializer):
    """删除购物车数据序列化器"""
    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate_sku_id(self, value):
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value


class CartSelectAllSerializer(serializers.Serializer):
    """购物车全选"""
    selected = serializers.BooleanField(label='全选')
