from rest_framework import serializers
from rest_framework.generics import ListAPIView
from .models import Photo

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image', 'latitude', 'longitude']

class PhotoLocationView(ListAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
