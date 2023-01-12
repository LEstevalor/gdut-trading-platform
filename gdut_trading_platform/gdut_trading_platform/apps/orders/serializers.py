from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class CartSKUSerializer(serializers.ModelSerializer):
    """购物车商品数据序列化器"""
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """订单结算数据序列化器"""
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class CommitOrderSerializer(serializers.ModelSerializer):
    """保存订单序列化器"""
    class Meta:
        model = OrderInfo
        fields = ['address', 'pay_method', 'order_id']
        # 但fields是双向的，注意前端只需要 address与pay_method的输入，不需要它输出，而order_id是要作为JSON返回的
        read_only_fields = ['order_id']   # 只序列化输出，不做反序列化，JSON只输出order_id
        extra_kwargs = {
            'address': {'write_only': True},
            'pay_method': {'write_only': True},
        }

    def create(self, validated_data):
        """保存订单"""
        # 获取当前保存订单需要的信息
        user = self.context['request'].user  # GenericAPIView里封装的context里的request字段
        # 因order_id需要，另外用user.id为保证订单号唯一（用户不可能一秒两单），且防止出现并发问题
        order_id = datetime.now().strftime('%Y%m%d%h%M%S') + '%09d' % user.id  # 取服务器时间，年月日时分秒
        address = validated_data.get('address')  # 前端传过来经反序列化的数据validated_data
        pay_method = validated_data.get('pay_method')
        # 订单状态，如果选择支付宝，那么以未支付状态unpaid保存，否则就是货到付款，以未寄出的状态unsend保存，选择都在数据库字段里
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])    # 加个括号就可以断行写了

        with transaction.atomic():  # 手动开启事务
            save_point = transaction.savepoint()  # 创建事务保存点
            try:
                # 保存订单基本信息OrderInfo (一)，除非有默认值，否则都有写上
                # 注意这里还没有save保存，后面total_count和total_amount补上再保存
                orderInfo = OrderInfo.objects.create(
                    order_id=order_id,   # 订单编号 —— 自定义创建（唯一且足够）：时间
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0.00'),
                    freight=Decimal('10.00'),  # 运费写死为10
                    pay_method=pay_method,
                    status=status,
                )

                # redis中读取购物车勾选的商品信息并遍历 (hash get all缩小hgetall)
                redis_conn = get_redis_connection('cart')
                cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)    # 取出来hash，k-v，k为商品id，v为数目
                selected_ids = redis_conn.smembers('selected_%d' % user.id)  # selected_user.id取出来选中商品id的集合

                # SKU.object.filter(id__in=selected_ids)  # queryset查询集的两大特性：惰性和缓存
                # 这里不建议这么写，因为查询集的缓存，多个用户同时抢一个商品会出现缓存的问题，导致数据错乱，我们应该保证数据都是最新的，用一取一
                for sku_id in selected_ids:
                    # 获取SKU对象
                    sku = SKU.objects.get(id=sku_id)
                    # 获取当前商品购买数量，注意读出来的是字符，而后面的比较是数字
                    buy_count = int(cart_dict_redis[sku_id])
                    # 该商品原本的库存和销量取出
                    cur_stock = sku.stock
                    cur_sales = sku.sales
                    # 判断库存，若有，则减少库存，增加销量
                    if buy_count > cur_stock:
                        # 有些公司直接在购物车就做此判断，跳出判断，也是一个方法（要么购物车判断，要么提交订单判断），
                        # 不过一般第二种，因为多个用户同时购物车就容易冲突，还是需要加判断，不过可以采取显示库存
                        raise serializers.ValidationError('库存不足')  # 跑异常，库存不足

                    new_stock = cur_stock - buy_count
                    new_sales = cur_sales + buy_count
                    sku.stock = new_stock
                    sku.sales = new_sales
                    sku.save()  # 保存SKU

                    # 修改SKU销量
                    spu = sku.goods
                    spu.sales = spu.sales + new_sales
                    spu.save()

                    # 保存订单商品信息 OrderGoods (多)，有默认值的不必要情况就不需写上
                    OrderGoods.objects.create(
                        order=orderInfo,  # 数据库字段定义的是外键，直接写模型
                        sku=sku,
                        count=buy_count,
                        price=sku.price,
                    )

                    # 累加计算总数目和总价
                    orderInfo.total_count = orderInfo.total_count + buy_count
                    orderInfo.total_amount = orderInfo.total_amount + buy_count * sku.price

                # 最后加入邮费和保存订单信息
                orderInfo.total_amount = orderInfo.total_amount + orderInfo.freight
                orderInfo.save()

            except Exception:
                transaction.savepoint_rollback(save_point)   # 回滚到保存点
                raise serializers.ValidationError('库存不足')  # 保证前端界面提示正常
            else:
                transaction.savepoint_commit(save_point)   # 提交事务

        # 清除购物车中已结算的商品

        # 返回订单模型对象
        return orderInfo  # 序列化的前端只需要order_id而已
