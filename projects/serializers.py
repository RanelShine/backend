# projects/serializers.py

from rest_framework import serializers
from .models import Project, Accountability, Comment
# Assurez-vous d'importer le sérialiseur de votre application `communes`
from communes.serializers import CommuneSerializer
# Importez get_user_model pour obtenir le modèle User actif dans votre projet Django
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle utilisateur, incluant des champs spécifiques
    pour les relations (ex: created_by, citizen, responded_by).
    """
    class Meta:
        model = User
        # Assurez-vous que ces champs existent sur votre modèle User personnalisé
        fields = ['id', 'email', 'nom', 'prenom', 'telephone', 'role']


class AuthorSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour l'auteur d'un commentaire.
    Il inclut les informations de base et un champ calculé pour l'URL de l'avatar.
    """
    # Ce champ calculé va appeler la méthode `get_avatar` pour obtenir l'URL de l'avatar.
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Incluez les champs nécessaires pour l'affichage de l'auteur dans le frontend.
        fields = ['id', 'email', 'nom', 'prenom', 'avatar']

    def get_avatar(self, obj):
        """
        Génère une URL d'avatar. Dans une application réelle, cela pourrait être :
        - L'URL d'un champ `ImageField` sur le modèle User (e.g., `obj.profile_picture.url`)
        - L'URL générée par un service d'avatar (e.g., Gravatar)
        - Une URL de placeholder basée sur l'initiale de l'utilisateur.
        
        Assurez-vous que `request` est passé au contexte du sérialiseur parent (CommentSerializer).
        """
        # Si votre modèle User a un champ 'avatar' réel (ImageField/FileField)
        if hasattr(obj, 'avatar') and obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url # Fallback si le contexte de la requête n'est pas disponible

        # Logique pour générer une URL de placeholder basée sur la première lettre
        initial = ''
        if obj.prenom:
            initial = obj.prenom[0].upper()
        elif obj.nom:
            initial = obj.nom[0].upper()
        elif obj.email:
            initial = obj.email[0].upper()
        else:
            initial = 'U' # Fallback générique si aucune information n'est disponible
            
        return f"https://placehold.co/32x32/cccccc/ffffff?text={initial}"
    
    def get_comment_count(self, obj):
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Commentaire.
    Il imbrique le `AuthorSerializer` pour inclure les détails de l'auteur du commentaire.
    """
    # Le champ 'author' est en lecture seule car il est défini par le backend (utilisateur connecté).
    # En utilisant `AuthorSerializer`, nous nous assurons que l'objet auteur complet est sérialisé.
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        # Incluez 'author' dans les champs à sérialiser pour qu'il apparaisse dans la réponse JSON.
        fields = ['id', 'project', 'author', 'text', 'created_at', 'updated_at']
        # Les champs suivants sont générés ou définis automatiquement par le backend lors de la création/mise à jour.
        read_only_fields = ['project', 'author', 'created_at', 'updated_at']

    def create(self, validated_data):
        """
        Crée une nouvelle instance de Commentaire.
        Les champs 'author' et 'project' sont gérés par la vue (`perform_create`).
        """
        return Comment.objects.create(**validated_data)


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'affichage d'une liste de projets.
    Il inclut des informations relationnelles imbriquées (commune, created_by)
    et des champs calculés (nombre de demandes de comptes, nombre de commentaires).
    """
    commune = CommuneSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    
    # Champ calculé pour le nombre de demandes de comptes associées au projet.
    accountability_count = serializers.SerializerMethodField()
    # Champ calculé pour le nombre de commentaires associés au projet.
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'status', 'commune',
            'start_date', 'end_date', 'budget', 'avancement',
            'file', 'created_at', 'created_by',
            'accountability_count', 'comments_count',
        ]

    def get_accountability_count(self, obj):
        # Utilise le related_name 'accountability_requests' défini sur la relation ForeignKey dans votre modèle Project
        return obj.accountability_requests.count()

    def get_comments_count(self, obj):
        # Utilise le related_name 'comments' défini sur la relation ForeignKey dans votre modèle Project
        return obj.comments.count()


class ProjectDetailSerializer(ProjectListSerializer):
    """
    Sérialiseur pour l'affichage détaillé d'un projet.
    Il hérite de ProjectListSerializer et ajoute des champs supplémentaires,
    notamment la liste complète des commentaires du projet.
    """
    # Le champ 'comments' est imbriqué en utilisant `CommentSerializer` pour afficher
    # tous les détails de chaque commentaire associé au projet.
    comments = CommentSerializer(many=True, read_only=True) 

    class Meta(ProjectListSerializer.Meta):
        # Utilise les champs de la classe parente et ajoute 'updated_at' et 'comments'.
        fields = ProjectListSerializer.Meta.fields + ['updated_at', 'comments']


class AccountabilitySerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les demandes de comptes, incluant les détails du citoyen,
    du répondeur et du projet associé.
    """
    citizen = UserBasicSerializer(read_only=True)
    responded_by = UserBasicSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True) # Utilise ProjectListSerializer pour les détails du projet

    class Meta:
        model = Accountability
        fields = [
            'id', 'project', 'citizen', 'question', 'response', 'status',
            'created_at', 'updated_at', 'responded_by', 'responded_at'
        ]
        # 'status', 'responded_by', 'responded_at' sont en lecture seule
        # car ils sont définis par le backend lors de la réponse à la demande.
        read_only_fields = ['status', 'responded_by', 'responded_at']


class AccountabilityCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une nouvelle demande de comptes.
    Le citoyen est automatiquement défini par l'utilisateur connecté.
    """
    class Meta:
        model = Accountability
        fields = ['project', 'question']

    def create(self, validated_data):
        # L'utilisateur faisant la requête est automatiquement défini comme le citoyen.
        validated_data['citizen'] = self.context['request'].user
        return super().create(validated_data)


class AccountabilityResponseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la réponse à une demande de comptes.
    Le répondeur est automatiquement défini par l'utilisateur connecté (CTD).
    """
    class Meta:
        model = Accountability
        fields = ['response']

    def update(self, instance, validated_data):
        # L'utilisateur faisant la requête est automatiquement défini comme le répondeur.
        validated_data['responded_by'] = self.context['request'].user
        return super().update(instance, validated_data)
