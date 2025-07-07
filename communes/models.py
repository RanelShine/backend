from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_migrate
from django.apps import apps
from django.dispatch import receiver

class Commune(models.Model):
    nom = models.CharField(_('nom'), max_length=100)
    region = models.CharField(_('region'), max_length=100)
    latitude = models.FloatField(_('latitude'), null=True, blank=True)
    longitude = models.FloatField(_('longitude'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('commune')
        verbose_name_plural = _('communes')
        ordering = ['nom']
        
    def __str__(self):
        return self.nom

@receiver(post_migrate)
def create_default_communes(sender, **kwargs):
    if sender.label == 'communes':  
        Commune = apps.get_model('communes', 'Commune')
        default_communes = [
            {
                'id': 1,
                'nom': 'Bafoussam I',
                'region': 'Ouest',
                'latitude': 5.475,  
                'longitude': 10.421  
            },
            {
                'id': 2,
                'nom': 'Bafoussam III',
                'region': 'Ouest',
                'latitude': 5.283333,  
                'longitude': 10.28333  
            },
            {
                'id': 3,
                'nom': 'Mandjou',
                'region': 'Est',
                'latitude': 4.600,  
                'longitude': 13.733  
            },
            {
                'id': 4,
                'nom': 'Foumbot',
                'region': 'Ouest',
                'latitude': 5.51269400,  
                'longitude': 10.63627000  
            },
            {
                'id': 5,
                'nom': 'Ngaoundéré III',
                'region': 'Adamaoua',
                'latitude': 7.404728932967782,  
                'longitude': 13.548091924166249  
            },
        ]
        for data in default_communes:
            Commune.objects.update_or_create(id=data['id'], defaults=data)
