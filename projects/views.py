# projects/views.py

from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
import os
import mimetypes
from django.http import HttpResponse, Http404
from django.conf import settings
from django.utils.encoding import smart_str
from wsgiref.util import FileWrapper
from .models import Project, Accountability, Comment # Importez le modèle Comment
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer,
    AccountabilitySerializer, AccountabilityCreateSerializer,
    AccountabilityResponseSerializer,
    CommentSerializer # Importez le CommentSerializer
)
from django.shortcuts import get_object_or_404 # Assurez-vous que ceci est importé

class IsCTDOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement aux CTD de créer/modifier des projets
    """
    def has_permission(self, request, view):
        # Allow read-only access for anyone (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write access only for authenticated users with role 'ctd'
        return request.user.is_authenticated and request.user.role == 'ctd'

    def has_object_permission(self, request, view, obj):
        # Allow read-only access for anyone (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Object-level permission: Only the CTD who created the project or belongs to the project's commune
        # can modify/delete it. Adjust as per your specific business logic.
        return request.user.is_authenticated and request.user.role == 'ctd' and request.user.commune == obj.commune


# NOUVEAU: Permissions personnalisées pour les commentaires
class IsCommentAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement à l'auteur du commentaire de le modifier/supprimer.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read-only access for anyone (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the author of the comment.
        return obj.author == request.user


# Project views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated]) # Ajout de cette ligne
def list_projects(request):
    """Liste tous les projets avec filtres optionnels, restreints à la commune de l'utilisateur"""
    
    # 1. Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentification requise pour lister les projets.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # 2. Récupérer la commune de l'utilisateur
    user_commune = request.user.commune
    if not user_commune:
        # Si l'utilisateur n'a pas de commune associée, il ne doit voir aucun projet
        return Response(
            {'error': 'Votre compte n\'est pas associé à une commune. Veuillez contacter l\'administrateur.'},
            status=status.HTTP_403_FORBIDDEN # Ou 200 avec une liste vide, selon la politique
        )

    # 3. Filtrer les projets par la commune de l'utilisateur
    queryset = Project.objects.select_related('commune', 'created_by').filter(commune=user_commune)
    
    # Filtrer par statut si spécifié
    status_param = request.query_params.get('status')
    if status_param:
        queryset = queryset.filter(status=status_param)
    
    # Recherche par titre ou description
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    queryset = queryset.order_by('-created_at')
    
    serializer = ProjectListSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsCTDOrReadOnly])
def create_project(request):
    """Crée un nouveau projet"""
    # Note: ProjectListSerializer est utilisé ici, mais pour la création,
    # vous devriez peut-être avoir un ProjectCreateSerializer qui gère mieux les champs
    # comme 'commune' et 'created_by' si non fournis dans le corps de la requête.
    serializer = ProjectListSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(
            created_by=request.user,
            commune=request.user.commune # Assurez-vous que l'utilisateur a une 'commune' associée
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated]) # Ajout de cette ligne
def project_detail(request, id):
    """Récupère les détails d'un projet spécifique, en vérifiant la commune de l'utilisateur"""
    try:
        # Utilise select_related pour les FK et prefetch_related pour les related_name (comme 'comments')
        project = Project.objects.select_related('commune', 'created_by').prefetch_related('comments').get(pk=id)
        
        # Vérification de la commune de l'utilisateur
        if not request.user.is_authenticated or request.user.commune != project.commune:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à voir les détails de ce projet car il n\'appartient pas à votre commune.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)
    except Project.DoesNotExist:
        return Response(
            {'error': 'Projet non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )

# Nouvelle vue pour le téléchargement sécurisé de fichiers
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_project_file(request, id):
    """Télécharge le fichier associé à un projet"""
    try:
        project = Project.objects.get(pk=id)
        
        # AJOUT : Vérification de la commune pour le téléchargement
        if not request.user.is_authenticated or request.user.commune != project.commune:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à télécharger ce fichier car le projet n\'appartient pas à votre commune.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if not project.file:
            return Response(
                {'error': 'Aucun fichier associé à ce projet'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Construire le chemin complet du fichier
        file_path = os.path.join(settings.MEDIA_ROOT, str(project.file))
        
        if not os.path.exists(file_path):
            return Response(
                {'error': 'Fichier non trouvé sur le serveur'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Déterminer le type MIME
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Créer la réponse HTTP avec le fichier
        response = HttpResponse(content_type=content_type)
        
        # Nom du fichier pour le téléchargement
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
        response['Content-Length'] = os.path.getsize(file_path)
        
        # Lire et retourner le fichier
        with open(file_path, 'rb') as f:
            response.write(f.read())
        
        return response
        
    except Project.DoesNotExist:
        return Response(
            {'error': 'Projet non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du téléchargement: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Mise à jour de la vue update_project pour mieux gérer les fichiers
@api_view(['PUT', 'PATCH'])
@permission_classes([IsCTDOrReadOnly])
def update_project(request, id):
    """Met à jour un projet existant"""
    try:
        project = Project.objects.get(pk=id)
        
        # Vérifier que l'utilisateur est un CTD de la bonne commune
        # La permission IsCTDOrReadOnly.has_object_permission gère déjà cela,
        # mais une double vérification explicite ne fait pas de mal pour la clarté.
        if request.user.role != 'ctd' or request.user.commune != project.commune:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à modifier ce projet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Gérer la suppression de l'ancien fichier si un nouveau est uploadé
        old_file = project.file
        
        serializer = ProjectDetailSerializer( # Utilisez ProjectDetailSerializer pour la mise à jour si vous le souhaitez
            project,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            # Supprimer l'ancien fichier si un nouveau est uploadé
            if 'file' in request.FILES and old_file:
                old_file_path = os.path.join(settings.MEDIA_ROOT, str(old_file))
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Project.DoesNotExist:
        return Response(
            {'error': 'Projet non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([IsCTDOrReadOnly])
def delete_project(request, id):
    """Supprime un projet"""
    try:
        project = Project.objects.get(pk=id)
        
        # Vérifier que l'utilisateur est un CTD de la bonne commune
        # La permission IsCTDOrReadOnly.has_object_permission gère déjà cela.
        if request.user.role != 'ctd' or request.user.commune != project.commune:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à supprimer ce projet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Supprimer le fichier associé si présent
        if project.file:
            file_path = os.path.join(settings.MEDIA_ROOT, str(project.file))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Project.DoesNotExist:
        return Response(
            {'error': 'Projet non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )

# Accountability views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_accountability(request):
    """Liste les demandes de comptes selon le rôle de l'utilisateur"""
    user = request.user
    
    # Les CTD voient toutes les demandes de leur commune
    if user.role == 'ctd':
        queryset = Accountability.objects.filter(
            project__commune=user.commune
        ).select_related('project', 'citizen', 'responded_by')
    # Les citoyens ne voient que leurs propres demandes
    else: # Ceci inclut également les utilisateurs sans rôle 'ctd' ou 'citizen' défini si vous avez d'autres rôles
        queryset = Accountability.objects.filter(
            citizen=user
        ).select_related('project', 'citizen', 'responded_by')
    
    serializer = AccountabilitySerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated]) # Assurez-vous que seul un utilisateur authentifié peut créer une demande
def create_accountability(request):
    """Crée une nouvelle demande de comptes"""
    serializer = AccountabilityCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def accountability_detail(request, id):
    """Récupère les détails d'une demande de comptes"""
    try:
        accountability = Accountability.objects.get(pk=id)
        
        # Vérifier les permissions
        if request.user.role == 'ctd':
            if request.user.commune != accountability.project.commune:
                return Response(
                    {'error': 'Vous n\'êtes pas autorisé à voir cette demande'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif accountability.citizen != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à voir cette demande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AccountabilitySerializer(accountability)
        return Response(serializer.data)
    except Accountability.DoesNotExist:
        return Response(
            {'error': 'Demande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsCTDOrReadOnly]) # Seuls les CTD peuvent répondre
def respond_accountability(request, id):
    """Répond à une demande de comptes"""
    try:
        accountability = Accountability.objects.get(pk=id)
        
        # Vérifier que l'utilisateur est un CTD de la bonne commune
        if request.user.role != 'ctd' or request.user.commune != accountability.project.commune:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à répondre à cette demande'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AccountabilityResponseSerializer(
            accountability,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(AccountabilitySerializer(accountability).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Accountability.DoesNotExist:
        return Response(
            {'error': 'Demande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )

# NOUVEAU: Vues pour les commentaires
class CommentListCreateView(generics.ListCreateAPIView):
    """
    Vue pour lister tous les commentaires d'un projet spécifique et créer un nouveau commentaire.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] 

    def get_queryset(self):
        """
        Filtrer les commentaires par l'ID du projet passé dans l'URL.
        Inclure les informations de l'auteur pour éviter N+1 requêtes.
        """
        project_id = self.kwargs['project_id']
        
        # Vérifier si le projet existe et si l'utilisateur y a accès
        project = get_object_or_404(Project, pk=project_id)
        
        # AJOUT : Vérification de la commune de l'utilisateur pour les commentaires
        # Permettre aux utilisateurs authentifiés de voir les commentaires uniquement pour les projets de leur commune
        if self.request.user.is_authenticated and self.request.user.commune != project.commune:
            # Si l'utilisateur est authentifié mais n'a pas accès à ce projet,
            # retourner un queryset vide pour ne pas afficher de commentaires.
            # Alternativement, vous pourriez lever une Http404 ou 403 ici.
            # Cependant, puisque c'est une liste, retourner un queryset vide est plus "doux".
            return Comment.objects.none() 

        # Récupérer les commentaires associés à ce projet existant et trier par date de création.
        # Utiliser select_related('author') pour optimiser la récupération des données de l'auteur.
        return Comment.objects.filter(project=project).select_related('author').order_by('-created_at')

    def perform_create(self, serializer):
        """
        Associer le commentaire à l'utilisateur connecté et au projet spécifié.
        """
        project_id = self.kwargs['project_id']
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            # Si le projet n'existe pas, renvoyer une erreur 404
            return Response(
                {"detail": "Projet non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # L'auteur du commentaire est l'utilisateur authentifié
        if not self.request.user.is_authenticated:
            return Response(
                {"detail": "Vous devez être authentifié pour commenter."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # AJOUT : Empêcher les commentaires sur des projets hors de la commune de l'utilisateur
        if self.request.user.commune != project.commune:
            return Response(
                {"detail": "Vous ne pouvez commenter que des projets de votre commune."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(author=self.request.user, project=project)

    def get_serializer_context(self):
        """
        Passe le contexte de la requête au sérialiseur.
        Ceci est essentiel pour que `AuthorSerializer.get_avatar` puisse construire des URLs absolues.
        """
        return {'request': self.request}


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, mettre à jour ou supprimer un commentaire spécifique.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsCommentAuthorOrReadOnly] # Cette permission gère déjà l'accès par auteur

    def get_object(self):
        """
        Récupère un commentaire en se basant sur le project_id et le pk du commentaire.
        """
        project_id = self.kwargs['project_id']
        pk = self.kwargs['pk']
        try:
            # Récupérer le commentaire et pré-charger les données de l'auteur et du projet.
            comment = Comment.objects.select_related('author', 'project').get(project_id=project_id, pk=pk)
            
            # AJOUT : Vérification de la commune du projet du commentaire
            if self.request.user.is_authenticated and self.request.user.commune != comment.project.commune:
                raise Http404("Commentaire non trouvé (accès restreint par commune).")

            self.check_object_permissions(self.request, comment) 
            return comment
        except Comment.DoesNotExist:
            raise Http404("Commentaire non trouvé.")

    def get_serializer_context(self):
        """
        Passe le contexte de la requête au sérialiseur pour `CommentDetailView` également.
        """
        return {'request': self.request}