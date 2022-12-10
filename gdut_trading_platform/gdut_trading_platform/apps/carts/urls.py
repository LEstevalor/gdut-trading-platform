from django.conf.urls import url

from .views import CartView, CartSelectedAllView

urlpatterns = [
    url(r'^carts/$', CartView.as_view()),           # 购物车增删改查
    url(r'^carts/selection/$', CartSelectedAllView.as_view())  # 购物车全选
]
