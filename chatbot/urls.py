# chatbot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_gemini, name='chat_gemini'),
]