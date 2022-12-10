from django.conf.urls import url
from rest_framework import routers

from . import views
from .views import UserDetailView, UserView, UsernameCountView, MobileCountView, EmailView, EmailVerifyView, \
    UserBrowsingHistoryView

urlpatterns = [
    url(r'^users/$', UserView.as_view()),   # 注册用户
    url(r'^usernames/(?P<username>\w{5,20})/count/$', UsernameCountView.as_view()),  # 判断用户名是否注册过
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', MobileCountView.as_view()),     # 判断电话是否注册过

    # url(r'^api/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),     # JWT登录
    # url(r'^api/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    # url(r'^api/token/verify/$', TokenVerifyView.as_view(), name='token_verify'),
    url(r'^api/token/$', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),     # JWT登录

    url(r'^user/$', UserDetailView.as_view()),     # 用户详情（用户中心）

    url(r'^email/$', EmailView.as_view()),     # 邮箱设置
    url(r'^emails/verification/$', EmailVerifyView.as_view()),    # 激活邮箱验证

    url(r'^browse_histories/$', UserBrowsingHistoryView.as_view()),   # 用户浏览历史

]

router = routers.DefaultRouter()
router.register(r'addresses', views.AddressViewSet, basename="addresses")
urlpatterns += router.urls

