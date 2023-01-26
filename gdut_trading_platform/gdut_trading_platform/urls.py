"""gdut_trading_platform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import xadmin
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # path('admin/', admin.site.urls),
    url(r'xadmin/', xadmin.site.urls),

    url(r'^', include('verifications.urls')),   # 发短信块模块
    url(r'^', include('users.urls')),           # 用户模块
    url(r'^', include('areas.urls')),           # 省市区处理模块
    url(r'^', include('goods.urls')),           # 商品模块
    url(r'^', include('carts.urls')),           # 购物车模块
    url(r'^', include('orders.urls')),           # 订单模块
    url(r'^', include('payment.urls')),          # 支付模块

    url(r'^ckeditor/', include('ckeditor_uploader.urls')),   # 富文本编辑器模块
]
