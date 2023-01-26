from django.conf.urls import url

from gdut_trading_platform.apps.payment import views

urlpatterns = [
    url(r'^orders/(?P<order_id>\d+)/payment/$', views.PaymentView.as_view()),  # 获取支付宝支付url
    url(r'^payment/status/$', views.PaymentStatusView.as_view()),  # 验证订单状态（支付成功，修改订单状态，保存支付宝交易号）
]
