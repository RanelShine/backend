from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nom', 'prenom', 'role', 'commune', 'is_active', 'is_verified')
    list_filter = ('is_active', 'is_verified', 'role')
    search_fields = ('email', 'nom', 'prenom')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'telephone')}),
        ('Informations de compte', {'fields': ('role', 'commune')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenom', 'password1', 'password2', 'role', 'commune', 'is_active', 'is_verified', 'is_staff', 'is_superuser'),
        }),
    )

# backend/communes/admin.py

from django.contrib import admin
from .models import Commune

@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'created_at')
    search_fields = ('nom',)