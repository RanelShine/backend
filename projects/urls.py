# projects/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Project routes
    path('', views.list_projects, name='project-list'),
    path('create/', views.create_project, name='project-create'),
    path('<int:id>/', views.project_detail, name='project-detail'),
    path('<int:id>/update/', views.update_project, name='project-update'),
    path('<int:id>/delete/', views.delete_project, name='project-delete'),
    path('<int:id>/download/', views.download_project_file, name='download-project-file'),
    
    # Accountability routes
    path('accountability/', views.list_accountability, name='accountability-list'),
    path('accountability/create/', views.create_accountability, name='accountability-create'),
    path('accountability/<int:id>/', views.accountability_detail, name='accountability-detail'),
    path('accountability/<int:id>/respond/', views.respond_accountability, name='accountability-respond'),


    path('<int:project_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list-create'),
    

    path('<int:project_id>/comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
]
