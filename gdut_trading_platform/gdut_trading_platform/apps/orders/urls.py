from django.conf.urls import url

from orders.views import OrderSettlementView, CommitOrderView

urlpatterns = [
    url(r'^orders/settlement/$', OrderSettlementView.as_view()),  # 获取订单
    url(r'^orders/$', CommitOrderView.as_view()),                 # 保存订单

]
