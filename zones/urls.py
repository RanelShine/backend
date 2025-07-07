# zones/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'zones', views.RiskZoneViewSet)
router.register(r'zone-images', views.RiskZoneImageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]