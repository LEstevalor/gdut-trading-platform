from rest_framework import serializers

from .models import Area


class AreaSerializer(serializers.ModelSerializer):
    """省序列化器"""
    class Meta:
        model = Area
        fields = ['id', 'name']


class SubSerializer(serializers.ModelSerializer):
    """返回⼦集数据的序列化器"""
    subs = AreaSerializer(many=True)

    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']



