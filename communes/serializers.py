from rest_framework import serializers
from .models import Commune

class CommuneSerializer(serializers.ModelSerializer):
    """
    Serializer pour les communes avec des champs supplémentaires pour la carte
    """
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = Commune
        fields = ['id', 'nom', 'region', 'latitude', 'longitude', 'coordinates', 'created_at', 'updated_at']
        
    def get_coordinates(self, obj):
        """
        Retourne les coordonnées au format attendu par le frontend
        """
        if obj.latitude is not None and obj.longitude is not None:
            return {
                'lat': obj.latitude,
                'lng': obj.longitude
            }
        return None
