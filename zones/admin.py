from django.contrib import admin
from .models import RiskZone

@admin.register(RiskZone)
class RiskZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'description', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'type', 'description')
        }),
        ('Géolocalisation', {
            'fields': ('coordinates',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )