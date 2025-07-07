# zones/models.py
from django.db import models
import json
import os


def zone_image_upload_path(instance, filename):
    """Fonction pour définir le chemin d'upload des images"""
    return f'zone_images/{instance.risk_zone.id}/{filename}'


class RiskZone(models.Model):
    RISK_TYPES = [
        ('innondations', 'Inondations'),
        ('secheresse', 'Sécheresse'),
        ('glissement de terrain', 'Glissement de terrain'),
        ('cours d\'eau', 'Cours d\'eau'),
        ('zone agricole', 'Zone agricole'),
        ('centres de santé', 'Centres de santé'),
        ('apparition des insectes nuisibles', 'Apparition des insectes nuisibles')
    ]
   
    name = models.CharField(max_length=200, verbose_name="Nom de la zone")
    type = models.CharField(max_length=50, choices=RISK_TYPES, verbose_name="Type de risque")
    description = models.TextField(verbose_name="Description")
   
    # Stockage des coordonnées du polygone en JSON
    coordinates = models.JSONField(
        help_text="Coordonnées du polygone au format GeoJSON"
    )
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    class Meta:
        verbose_name = "Zone à risque"
        verbose_name_plural = "Zones à risque"
        ordering = ['-created_at']
   
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
   
    @property
    def polygon_geojson(self):
        """Retourne les coordonnées au format GeoJSON Polygon"""
        return {
            "type": "Polygon",
            "coordinates": self.coordinates
        }
   
    def get_center_coordinates(self):
        """Calcule le centre approximatif du polygone"""
        if not self.coordinates or not self.coordinates[0]:
            return None
       
        coords = self.coordinates[0]  # Premier anneau du polygone
        total_lat = sum(coord[1] for coord in coords)
        total_lng = sum(coord[0] for coord in coords)
       
        return [total_lat / len(coords), total_lng / len(coords)]
    
    def get_images(self):
        """Retourne toutes les images associées à cette zone"""
        return self.images.all()
    
    def get_images_urls(self):
        """Retourne les URLs des images pour l'API"""
        return [image.image.url for image in self.images.all() if image.image]


class RiskZoneImage(models.Model):
    """Modèle pour stocker les images associées aux zones à risque"""
    risk_zone = models.ForeignKey(
        RiskZone, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Zone à risque"
    )
    image = models.ImageField(
        upload_to=zone_image_upload_path,
        verbose_name="Image"
    )
    caption = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Légende"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Image de zone à risque"
        verbose_name_plural = "Images de zones à risque"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Image pour {self.risk_zone.name}"
    
    def delete(self, *args, **kwargs):
        """Supprime le fichier image du système de fichiers lors de la suppression"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)