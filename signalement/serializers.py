#signalement/serializers.py
from rest_framework import serializers
from .models import Signalement
from accounts.models import User

class SignalementSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)
    utilisateur_email = serializers.CharField(source='utilisateur.email', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    type_signalement_display = serializers.CharField(source='get_type_signalement_display', read_only=True)
    
    class Meta:
        model = Signalement
        fields = [
            'id', 'objet', 'description', 'date_signalement', 'date_resolution',
            'statut', 'statut_display', 'localisation', 'type_signalement',
            'type_signalement_display', 'utilisateur', 'utilisateur_nom', 'utilisateur_email',
            'photo_id', 'commune'
        ]
        read_only_fields = ['id', 'date_signalement', 'utilisateur']

class SignalementCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de signalements - Accessible à tous les utilisateurs authentifiés"""
    class Meta:
        model = Signalement
        fields = [
            'objet', 'description', 'localisation', 'type_signalement', 'photo_id', 'commune'
        ]
    
    def validate_type_signalement(self, value):
        valid_types = [choice[0] for choice in Signalement.TYPE_SIGNALLEMENT_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Type de signalement invalide. Choisissez parmi: {valid_types}")
        return value

class SignalementUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification par les citoyens (propriétaires) - Champs limités"""
    class Meta:
        model = Signalement
        fields = [
            'objet', 'description', 'localisation', 'type_signalement', 'photo_id'
        ]
    
    def validate_type_signalement(self, value):
        valid_types = [choice[0] for choice in Signalement.TYPE_SIGNALLEMENT_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Type de signalement invalide. Choisissez parmi: {valid_types}")
        return value
    
    def validate(self, attrs):
        # Les citoyens ne peuvent pas modifier le statut ou la date de résolution
        # Ces champs sont automatiquement exclus du Meta.fields
        return attrs

class SignalementAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification par les ctdet administrateurs - Tous les champs"""
    class Meta:
        model = Signalement
        fields = [
            'objet', 'description', 'localisation', 'type_signalement',
            'statut', 'date_resolution', 'photo_id', 'commune'
        ]
    
    def validate_statut(self, value):
        valid_statuts = [choice[0] for choice in Signalement.STATUT_CHOICES]
        if value not in valid_statuts:
            raise serializers.ValidationError(f"Statut invalide. Choisissez parmi: {valid_statuts}")
        return value
    
    def validate_type_signalement(self, value):
        valid_types = [choice[0] for choice in Signalement.TYPE_SIGNALLEMENT_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Type de signalement invalide. Choisissez parmi: {valid_types}")
        return value
    
    def update(self, instance, validated_data):
        # Mise à jour automatique de la date de résolution si le statut passe à "traité"
        if validated_data.get('statut') == 'traite' and not validated_data.get('date_resolution'):
            from django.utils import timezone
            validated_data['date_resolution'] = timezone.now()
        return super().update(instance, validated_data)

class SignalementStatutSerializer(serializers.ModelSerializer):
    """Serializer spécialement pour la modification du statut uniquement - ctd et administrateurs"""
    class Meta:
        model = Signalement
        fields = ['statut', 'date_resolution']
    
    def validate_statut(self, value):
        valid_statuts = [choice[0] for choice in Signalement.STATUT_CHOICES]
        if value not in valid_statuts:
            raise serializers.ValidationError(f"Statut invalide. Choisissez parmi: {valid_statuts}")
        return value
    
    def update(self, instance, validated_data):
        # Si le statut passe à "traité", on peut automatiquement définir la date de résolution
        if validated_data.get('statut') == 'traite' and not validated_data.get('date_resolution'):
            from django.utils import timezone
            validated_data['date_resolution'] = timezone.now()
        return super().update(instance, validated_data)

class SignalementListSerializer(serializers.ModelSerializer):
    """Serializer optimisé pour les listes de signalements"""
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    type_signalement_display = serializers.CharField(source='get_type_signalement_display', read_only=True)
    
    class Meta:
        model = Signalement
        fields = [
            'id', 'objet', 'date_signalement', 'statut', 'statut_display', 
            'type_signalement', 'type_signalement_display', 'utilisateur_nom', 
            'commune', 'localisation'
        ]

class SignalementStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des signalements"""
    total = serializers.IntegerField()
    en_attente = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    traite = serializers.IntegerField()
    rejete = serializers.IntegerField()
    par_type = serializers.DictField()
    par_commune = serializers.DictField(required=False)
    
class SignalementFilterSerializer(serializers.Serializer):
    """Serializer pour valider les filtres de recherche"""
    statut = serializers.ChoiceField(choices=Signalement.STATUT_CHOICES, required=False)
    type_signalement = serializers.ChoiceField(choices=Signalement.TYPE_SIGNALLEMENT_CHOICES, required=False)
    commune = serializers.CharField(max_length=100, required=False)
    utilisateur = serializers.IntegerField(required=False)
    date_debut = serializers.DateTimeField(required=False)
    date_fin = serializers.DateTimeField(required=False)