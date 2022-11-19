from django.conf.urls import url
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from . import views

urlpatterns = [
    url(r'^users/$', views.UserView.as_view()),   # 注册用户
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),  # 判断用户名是否注册过
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),     # 判断电话是否注册过

    url(r'^api/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),     # JWT登录
    url(r'^api/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    url(r'^api/token/verify/$', TokenVerifyView.as_view(), name='token_verify'),

]

"""
# JWT登录（jwt版本的，上面是Simple jwt版本的）
from rest_framework_jwt.views import obtain_jwt_token
url(r'^authorizations/$', obtain_jwt_token),
    
obtain_jwt_token = ObtainJSONWebToken.as_view()
refresh_jwt_token = RefreshJSONWebToken.as_view()
verify_jwt_token = VerifyJSONWebToken.as_view()
"""

