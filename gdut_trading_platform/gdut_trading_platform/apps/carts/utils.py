import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user_id, response):
    """
    合并请求用户的购物车数据，将未登录保存在cookie里的保存到redis中
    遇到cookie与redis中出现相同的商品时以cookie数据为主，覆盖redis中的数据
    :param request: 用户的请求对象
    :param user_id: 当前登录的用户的ID（从序列化器取出）
    :param response: 响应对象，用于清楚购物车cookie
    :return:
    """
    # 获取cookie中的购物车
    cookie_cart = request.COOKIES.get('cart')
    if not cookie_cart:
        return response

    cookie_cart = pickle.loads(base64.b64decode(cookie_cart.encode()))
    cart = {}                          # 用于保存向redis购物车商品数量hash添加数据的字典(id-count)
    redis_cart_selected_add = []       # 记录redis勾选状态中应该增加的sku_id —— selected
    redis_cart_selected_remove = []    # 记录redis勾选状态中应该删除的sku_id

    for sku_id, count_selected_dict in cookie_cart.items():
        # 字典存储
        cart[sku_id] = count_selected_dict['count']
        # 列表存储
        if count_selected_dict['selected']:
            redis_cart_selected_add.append(sku_id)
        else:
            redis_cart_selected_remove.append(sku_id)

    if cart:
        redis_conn = get_redis_connection('cart')
        pl = redis_conn.pipeline()
        pl.hmset("cart_%d" % user_id, cart)
        if redis_cart_selected_add:
            # 对应set，传列表用*；对应hash，传字典直接传输即可
            pl.sadd('selected_%d' % user_id, *redis_cart_selected_add)
        if redis_cart_selected_remove:
            pl.srem('selected_%d' % user_id, *redis_cart_selected_remove)
        pl.execute()

    response.delete_cookie('cart')
    return response
