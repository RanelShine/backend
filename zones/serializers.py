# zones/serializers.py
from rest_framework import serializers
from .models import RiskZone, RiskZoneImage


class RiskZoneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskZoneImage
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class RiskZoneSerializer(serializers.ModelSerializer):
    images = RiskZoneImageSerializer(many=True, read_only=True)
    images_urls = serializers.SerializerMethodField()
    
    class Meta:
        model = RiskZone
        fields = [
            'id', 'name', 'type', 'description', 'coordinates', 
            'created_at', 'updated_at', 'images', 'images_urls'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_images_urls(self, obj):
        """Retourne les URLs des images"""
        request = self.context.get('request')
        if request and obj.images.exists():
            return [
                request.build_absolute_uri(image.image.url) 
                for image in obj.images.all() 
                if image.image
            ]
        return []
    
    def create(self, validated_data):
        """Crée une zone avec gestion des images"""
        # Les images sont gérées séparément via l'upload
        return super().create(validated_data)