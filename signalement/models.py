#signalement/models.py
from django.db import models
from accounts.models import User
from communes.models import Commune

class Signalement(models.Model):
    TYPE_SIGNALLEMENT_CHOICES = [
        ('dechets', 'Déchets'),
        ('pollution', 'Pollution'),
        ('climat', 'Climat'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('traite', 'Traité'),
        ('rejeté', 'Rejeté'),
        ('suspendu', 'Suspendu'),
    ]
    
    objet = models.CharField(max_length=255)
    description = models.TextField()
    date_signalement = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='en_attente')
    localisation = models.CharField(max_length=255)
    type_signalement = models.CharField(max_length=50, choices=TYPE_SIGNALLEMENT_CHOICES)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    photo_id = models.IntegerField(null=True, blank=True)
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-date_signalement']
    
    def __str__(self):
        return f"{self.objet} - {self.type_signalement} ({self.get_statut_display()})"