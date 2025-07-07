# zones/apps.py
from django.apps import AppConfig

class ZonesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zones'
    verbose_name = 'Zones à risque'