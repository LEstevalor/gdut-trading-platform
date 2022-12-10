from django.conf.urls import url

from .views import CartView, CartSelectedAllView

urlpatterns = [
    url(r'^carts/$', CartView.as_view()),           # ���ﳵ��ɾ�Ĳ�
    url(r'^carts/selection/$', CartSelectedAllView.as_view())  # ���ﳵȫѡ
]
