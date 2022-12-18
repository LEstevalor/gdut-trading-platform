from django.conf.urls import url

from orders.views import OrderSettlementView

urlpatterns = [
    url(r'^orders/settlement/$', OrderSettlementView.as_view()),  # ªÒ»°∂©µ•
]