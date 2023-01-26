from django.conf.urls import url

from goods import views
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/skus/', views.SKUListView.as_view()),
]

router = DefaultRouter()
router.register('skus/search', views.SKUSearchViewSet, basename='skus_search')

urlpatterns += router.urls
