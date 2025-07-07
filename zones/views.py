# zones/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import RiskZone, RiskZoneImage
from .serializers import RiskZoneSerializer, RiskZoneImageSerializer


class RiskZoneViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = RiskZone.objects.all()
    serializer_class = RiskZoneSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, pk=None):
        """Endpoint pour uploader des images pour une zone spécifique"""
        zone = get_object_or_404(RiskZone, pk=pk)
        images = request.FILES.getlist('images')  # Récupère toutes les images
        
        if not images:
            return Response(
                {'error': 'Aucune image fournie'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_images = []
        for image in images:
            # Créer une instance d'image pour chaque fichier
            zone_image = RiskZoneImage.objects.create(
                risk_zone=zone,
                image=image,
                caption=request.data.get('caption', '')
            )
            uploaded_images.append(RiskZoneImageSerializer(zone_image).data)
        
        return Response({
            'message': f'{len(uploaded_images)} image(s) uploadée(s) avec succès',
            'images': uploaded_images
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Récupère toutes les images d'une zone"""
        zone = get_object_or_404(RiskZone, pk=pk)
        images = zone.images.all()
        serializer = RiskZoneImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Supprime une image spécifique d'une zone"""
        zone = get_object_or_404(RiskZone, pk=pk)
        image = get_object_or_404(RiskZoneImage, pk=image_id, risk_zone=zone)
        image.delete()
        return Response({'message': 'Image supprimée avec succès'}, status=status.HTTP_204_NO_CONTENT)


class RiskZoneImageViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les images individuellement"""
    queryset = RiskZoneImage.objects.all()
    serializer_class = RiskZoneImageSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]