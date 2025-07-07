# signalement/views.py
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from photos.models import Photo
from .models import Signalement
from .serializers import (
    SignalementSerializer, 
    SignalementCreateSerializer, 
    SignalementUpdateSerializer,
    SignalementStatutSerializer,
    SignalementAdminUpdateSerializer
)
from accounts.models import User
import traceback

# CREATE - Création d'un signalement
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def create_signalement(request):
    try:
        serializer = SignalementCreateSerializer(data=request.data)
        if serializer.is_valid():
            photo_id = request.data.get('photo_id')
            if photo_id:
                try:
                    Photo.objects.get(id=photo_id)
                except Photo.DoesNotExist:
                    return Response({'error': 'Photo non trouvée'}, status=status.HTTP_400_BAD_REQUEST)
            
            
            commune_user = getattr(request.user, 'commune', None)
            
            # Créer le signalement avec utilisateur et commune si disponible
            signalement = serializer.save(utilisateur=request.user, commune=commune_user)
            
            response_serializer = SignalementSerializer(signalement)
            return Response({
                'message': 'Signalement créé avec succès',
                'signalement': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# READ - Liste de tous les signalements
@api_view(['GET'])
def list_signalements(request):
    """Lister les signalements avec filtres selon le rôle de l'utilisateur"""
    try:
        signalements = Signalement.objects.all()
        
        # Filtrage selon le rôle de l'utilisateur
        if request.user.is_authenticated:
            if request.user.role == 'citoyen':
                # Les citoyens ne voient que leurs propres signalements
                signalements = signalements.filter(utilisateur=request.user)
            elif request.user.role == 'ctd':
                # Les ctd municipaux voient les signalements de leur commune
                if hasattr(request.user, 'commune') and request.user.commune:
                    signalements = signalements.filter(commune=request.user.commune)
                else:
                    # Si le CTD n'a pas de commune assignée, retourner une liste vide
                    signalements = signalements.none()
            elif request.user.role == 'admin':
                # Les administrateurs voient tous les signalements (pas de filtre)
                pass
            else:
                # Rôle non reconnu - traiter comme un utilisateur non authentifié
                signalements = signalements.filter(statut='en_cours')
        else:
            # Utilisateurs non authentifiés : signalements publics seulement
            signalements = signalements.filter(statut='en_cours')
        
        # Filtres optionnels
        statut = request.GET.get('statut')
        type_signalement = request.GET.get('type')
        utilisateur_id = request.GET.get('utilisateur')
        commune = request.GET.get('commune')
        
        if statut:
            signalements = signalements.filter(statut=statut)
        if type_signalement:
            signalements = signalements.filter(type_signalement=type_signalement)
        if utilisateur_id and (request.user.is_authenticated and request.user.role in ['admin', 'ctd']):
            signalements = signalements.filter(utilisateur_id=utilisateur_id)
        if commune and (request.user.is_authenticated and request.user.role in ['admin', 'ctd']):
            signalements = signalements.filter(commune=commune)
            
        serializer = SignalementSerializer(signalements, many=True)
        return Response({
            'count': signalements.count(),
            'signalements': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# READ - Détails d'un signalement spécifique
@api_view(['GET'])
def detail_signalement(request, id):
    """Obtenir les détails d'un signalement selon les permissions de rôle"""
    try:
        signalement = Signalement.objects.get(pk=id)
        
        # Vérification des permissions de lecture
        if request.user.is_authenticated:
            if request.user.role == 'Citoyens':
                # Les citoyens peuvent voir tous les signalements publics (statut 'en_cours')
                # ET leurs propres signalements (peu importe le statut)
                if signalement.utilisateur != request.user and signalement.statut != 'en_cours':
                    return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
            elif request.user.role == 'ctd':
                # Un CTD peut voir les signalements de sa commune ET ses propres signalements
                if hasattr(request.user, 'commune') and request.user.commune:
                    # Autoriser si c'est un signalement de sa commune OU son propre signalement
                    if signalement.commune != request.user.commune and signalement.utilisateur != request.user:
                        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
                else:
                    # Si le CTD n'a pas de commune, il peut au moins voir ses propres signalements
                    if signalement.utilisateur != request.user:
                        return Response({'error': 'Aucune commune assignée'}, status=status.HTTP_403_FORBIDDEN)
            
            elif request.user.role == 'admin':
                # Les administrateurs peuvent voir tous les signalements
                pass
            else:
                # Rôle non reconnu - traiter comme un utilisateur non authentifié
                if signalement.statut != 'en_cours':
                    return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Utilisateurs non authentifiés : seulement les signalements publics
            if signalement.statut != 'en_cours':
                return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SignalementSerializer(signalement)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Signalement.DoesNotExist:
        return Response({'error': 'Signalement non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# UPDATE - Modification complète d'un signalement
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def update_signalement(request, id):
    """Modifier un signalement selon les permissions de rôle."""
    try:
        signalement = Signalement.objects.get(pk=id)

        # Cas 1 : Utilisateur CTD
        if request.user.role == 'ctd':
            if signalement.utilisateur != request.user:
                return Response(
                    {'error': 'Vous n\'êtes pas autorisé à modifier ce signalement'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = SignalementUpdateSerializer(signalement, data=request.data, partial=True)

        # Cas 2 : Utilisateur citoyen
        elif request.user.role == 'citoyen':
            if signalement.utilisateur != request.user:
                return Response(
                    {'error': 'Vous n\'êtes pas autorisé à modifier ce signalement'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not hasattr(request.user, 'commune') or not request.user.commune:
                return Response(
                    {'error': 'Aucune commune assignée à cet utilisateur'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = SignalementUpdateSerializer(signalement, data=request.data, partial=True)

        # Cas 3 : Administrateur
        elif request.user.role == 'admin':
            serializer = SignalementAdminUpdateSerializer(signalement, data=request.data, partial=True)

        # Cas 4 : Rôle inconnu
        else:
            return Response({'error': 'Rôle non autorisé'}, status=status.HTTP_403_FORBIDDEN)

        # Vérification des données
        if serializer.is_valid():
            photo_id = request.data.get('photo_id')
            if photo_id:
                try:
                    Photo.objects.get(id=photo_id)
                except Photo.DoesNotExist:
                    return Response({'error': 'Photo non trouvée'}, status=status.HTTP_400_BAD_REQUEST)

            signalement = serializer.save()
            response_serializer = SignalementSerializer(signalement)
            return Response({
                'message': 'Signalement modifié avec succès',
                'signalement': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Signalement.DoesNotExist:
        return Response({'error': 'Signalement non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# UPDATE - Modification du statut uniquement
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def update_signalement_statut(request, id):
    """Modifier le statut d'un signalement - Réservé aux ctd et administrateurs"""
    try:
        signalement = Signalement.objects.get(pk=id)
        
        # Vérification des permissions - Seuls les CTD et administrateurs peuvent modifier le statut
        if request.user.role == 'citoyen':
            return Response({'error': 'Vous n\'êtes pas autorisé à modifier le statut'}, 
                          status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'ctd':
            # Les ctd peuvent modifier les signalements de leur commune
            if hasattr(request.user, 'commune') and request.user.commune:
                if signalement.commune != request.user.commune:
                    return Response({'error': 'Vous n\'êtes pas autorisé à modifier ce signalement'}, 
                                  status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Aucune commune assignée'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'admin':
            # Les administrateurs peuvent modifier tous les statuts
            pass
        else:
            return Response({'error': 'Rôle non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SignalementStatutSerializer(signalement, data=request.data, partial=True)
        if serializer.is_valid():
            signalement = serializer.save()
            response_serializer = SignalementSerializer(signalement)
            return Response({
                'message': 'Statut modifié avec succès',
                'signalement': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Signalement.DoesNotExist:
        return Response({'error': 'Signalement non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# DELETE - Suppression d’un signalement
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def delete_signalement(request, id):
    try:
        signalement = Signalement.objects.get(pk=id)

        # Seul le propriétaire ou l'admin peut supprimer
        if request.user != signalement.utilisateur and request.user.role != 'admin':
            return Response({'error': 'Vous n\'êtes pas autorisé à supprimer ce signalement'}, status=status.HTTP_403_FORBIDDEN)

        signalement.delete()
        return Response({'message': 'Signalement supprimé avec succès'}, status=status.HTTP_204_NO_CONTENT)

    except Signalement.DoesNotExist:
        return Response({'error': 'Signalement non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Endpoint pour obtenir les choix disponibles
@api_view(['GET'])
def get_signalement_choices(request):
    """Obtenir les choix disponibles pour les types et statuts"""
    return Response({
        'types_signalement': [{'value': choice[0], 'label': choice[1]} for choice in Signalement.TYPE_SIGNALLEMENT_CHOICES],
        'statuts': [{'value': choice[0], 'label': choice[1]} for choice in Signalement.STATUT_CHOICES]
    }, status=status.HTTP_200_OK)

# READ - Signalements de l'utilisateur connecté
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def mes_signalements(request):
    """Lister les signalements de l'utilisateur connecté"""
    try:
        signalements = Signalement.objects.filter(utilisateur=request.user)
        
        # Filtres optionnels
        statut = request.GET.get('statut')
        type_signalement = request.GET.get('type')
        
        if statut:
            signalements = signalements.filter(statut=statut)
        if type_signalement:
            signalements = signalements.filter(type_signalement=type_signalement)
            
        serializer = SignalementSerializer(signalements, many=True)
        return Response({
            'count': signalements.count(),
            'signalements': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# READ - Signalements par commune (pour les ctd)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def signalements_commune(request):
    """Lister les signalements d'une commune - Réservé aux ctd et administrateurs"""
    try:
        if request.user.role == 'citoyen':
            return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.user.role == 'ctd':
            # Les ctd voient les signalements de leur commune
            if not (hasattr(request.user, 'commune') and request.user.commune):
                return Response({'error': 'Aucune commune assignée'}, status=status.HTTP_400_BAD_REQUEST)
            signalements = Signalement.objects.filter(commune=request.user.commune)
        elif request.user.role == 'admin':
            # Les administrateurs peuvent spécifier une commune ou voir tous
            commune = request.GET.get('commune')
            if commune:
                signalements = Signalement.objects.filter(commune=commune)
            else:
                signalements = Signalement.objects.all()
        else:
            return Response({'error': 'Rôle non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        # Filtres optionnels
        statut = request.GET.get('statut')
        type_signalement = request.GET.get('type')
        
        if statut:
            signalements = signalements.filter(statut=statut)
        if type_signalement:
            signalements = signalements.filter(type_signalement=type_signalement)
            
        serializer = SignalementSerializer(signalements, many=True)
        return Response({
            'count': signalements.count(),
            'signalements': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# READ - Statistiques des signalements (pour les administrateurs et ctd)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def statistiques_signalements(request):
    """Obtenir les statistiques des signalements selon le rôle"""
    try:
        if request.user.role == 'citoyen':
            return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.user.role == 'ctd':
            # Statistiques pour la commune du ctd
            if not (hasattr(request.user, 'commune') and request.user.commune):
                return Response({'error': 'Aucune commune assignée'}, status=status.HTTP_400_BAD_REQUEST)
            signalements = Signalement.objects.filter(commune=request.user.commune)
        elif request.user.role == 'admin':
            # Statistiques globales
            signalements = Signalement.objects.all()
        else:
            return Response({'error': 'Rôle non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        # Calcul des statistiques
        stats = {
            'total': signalements.count(),
            'en_attente': signalements.filter(statut='en_attente').count(),
            'en_cours': signalements.filter(statut='en_cours').count(),
            'traite': signalements.filter(statut='traite').count(),
            'rejete': signalements.filter(statut='rejete').count(),
        }
        
        # Statistiques par type
        types_stats = {}
        for type_choice in Signalement.TYPE_SIGNALLEMENT_CHOICES:
            type_code = type_choice[0]
            types_stats[type_code] = signalements.filter(type_signalement=type_code).count()
        
        stats['par_type'] = types_stats
        
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)