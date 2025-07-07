from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('communes', views.CommuneViewSet, basename='commune')

urlpatterns = [
    path('', include(router.urls)),
]