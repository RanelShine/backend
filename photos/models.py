#photos/models.py
from django.db import models

class Photo(models.Model):
    image = models.ImageField(upload_to='photos/')
    latitude = models.FloatField()
    longitude = models.FloatField()
    date_uploaded = models.DateTimeField(auto_now_add=True)
