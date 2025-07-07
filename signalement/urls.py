#signalement/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # CREATE
    path('create/', views.create_signalement, name='create-signalement'),
    
    # READ
    path('liste/', views.list_signalements, name='list-signalements'),
    path('detail/<int:id>/', views.detail_signalement, name='detail-signalement'),
    path('mes-signalements/', views.mes_signalements, name='mes-signalements'),
    
    # UPDATE
    path('update/<int:id>/', views.update_signalement, name='update-signalement'),
    path('update-statut/<int:id>/', views.update_signalement_statut, name='update-signalement-statut'),
    
    # DELETE
    path('delete/<int:id>/', views.delete_signalement, name='delete-signalement'),
    
    # UTILITAIRE
    path('choices/', views.get_signalement_choices, name='signalement-choices'),
]