from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Commune
from .serializers import CommuneSerializer

class CommuneViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les communes.
    Permet la lecture pour tous les utilisateurs authentifiés,
    mais restreint la modification aux administrateurs.
    """
    queryset = Commune.objects.all().order_by('nom')
    serializer_class = CommuneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Seuls les administrateurs peuvent modifier les communes.
        La lecture est autorisée pour tous les utilisateurs authentifiés.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """
        Liste toutes les communes.
        Pour les CTD, filtre pour ne montrer que leur commune.
        """
        queryset = self.get_queryset()
        
        # Si l'utilisateur est un CTD, ne renvoyer que sa commune
        if request.user.role == 'ctd' and request.user.commune:
            queryset = queryset.filter(id=request.user.commune.id)

        # Filtres optionnels
        region = request.query_params.get('region', None)
        search = request.query_params.get('search', None)
        has_coordinates = request.query_params.get('has_coordinates', None)

        if region:
            queryset = queryset.filter(region=region)
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | 
                Q(region__icontains=search)
            )
        if has_coordinates:
            queryset = queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Renvoie la commune de l'utilisateur connecté s'il en a une.
        """
        if request.user.commune:
            serializer = self.get_serializer(request.user.commune)
            return Response(serializer.data)
        return Response(
            {'detail': 'Aucune commune associée'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'])
    def regions(self, request):
        """
        Liste toutes les régions distinctes.
        """
        regions = Commune.objects.values_list('region', flat=True).distinct()
        return Response(list(regions))

    @action(detail=True, methods=['get'])
    def signalements(self, request, pk=None):
        """
        Liste tous les signalements d'une commune.
        """
        commune = self.get_object()
        
        # Vérifier les permissions
        if request.user.role == 'ctd' and request.user.commune != commune:
            return Response(
                {'detail': 'Accès non autorisé à cette commune'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Import ici pour éviter les imports circulaires
        from signalement.models import Signalement
        from signalement.serializers import SignalementListSerializer

        signalements = Signalement.objects.filter(commune=commune)
        serializer = SignalementListSerializer(signalements, many=True)
        
        return Response({
            'count': signalements.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Crée une nouvelle commune.
        Réservé aux administrateurs.
        """
        if not request.user.is_staff:
            return Response(
                {'detail': 'Seuls les administrateurs peuvent créer des communes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Met à jour une commune.
        Réservé aux administrateurs.
        """
        if not request.user.is_staff:
            return Response(
                {'detail': 'Seuls les administrateurs peuvent modifier des communes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime une commune.
        Réservé aux administrateurs.
        """
        if not request.user.is_staff:
            return Response(
                {'detail': 'Seuls les administrateurs peuvent supprimer des communes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
