#photos/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import Photo
from .serializers import PhotoSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# POST : Envoie une photo avec lat/lon
class UploadPhotoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save()
            # Retourne les données du serializer, notamment l'id
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("Erreurs serializer :", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET : Liste toutes les photos avec leurs coordonnées
def photo_locations(request):
    data = [
        {
            'id': photo.id,
            'image_url': request.build_absolute_uri(photo.image.url),
            'latitude': photo.latitude,
            'longitude': photo.longitude,
            'date_uploaded': photo.date_uploaded.strftime('%Y-%m-%d %H:%M:%S')
        }
        for photo in Photo.objects.all()
    ]
    return JsonResponse(data, safe=False)
class PhotoLocationView(APIView):
    def get(self, request):
        data = [
            {
                'id': photo.id,
                'image_url': request.build_absolute_uri(photo.image.url),
                'latitude': photo.latitude,
                'longitude': photo.longitude,
                'date_uploaded': photo.date_uploaded.strftime('%Y-%m-%d %H:%M:%S')
            }
            for photo in Photo.objects.all()
        ]
        return Response(data, status=status.HTTP_200_OK)