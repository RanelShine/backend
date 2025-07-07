# urls.py
from django.urls import path
from .views import PhotoLocationView, UploadPhotoView

urlpatterns = [
    path('upload-photo/', UploadPhotoView.as_view(), name='upload-photo'),
    path('locations/', PhotoLocationView.as_view(), name='photo_locations'),
]
