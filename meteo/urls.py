# meteo/urls.py
from django.urls import path
from . import views # Importe les vues de l'application meteo

urlpatterns = [
    path('weather/', views.get_weather, name='get_weather'),
    path('pollution/', views.get_pollution, name='get_pollution'),
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
    path('educational/', views.get_educational_message, name='get_educational_message'),
]