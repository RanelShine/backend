from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from .utils import send_verification_email
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, UserRegisterSerializer, LoginSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Création de l'utilisateur (is_active=False par défaut dans create_user())
            user = serializer.save()
            
            # Génération du code + sauvegarde
            code = user.set_verification_code()
            
            # Envoi de l'email
            send_verification_email(user.email, code)
            
            return Response({
                'success': True,
                'message': 'Compte créé. Vérifiez votre email pour activer votre compte.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyAccountView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        code  = request.data.get('code')
        try:
            user = User.objects.get(email=email, verification_code=code)
            if timezone.now() > user.code_expiration:
                return Response({'success': False, 'message': 'Code expiré.'}, status=400)
            user.is_active       = True
            user.is_verified     = True
            user.verification_code = None
            user.code_expiration   = None
            user.save()
            return Response({'success': True, 'message': 'Compte activé.'}, status=200)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'Code invalide.'}, status=400)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Crée un refresh et access token
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'user': UserSerializer(user).data,
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Récupérer les tokens
            refresh_token = request.data.get('refresh_token')
            access_token = request.data.get('access_token')

            if refresh_token:
                try:
                    # Invalider le refresh token
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as e:
                    print(f"Erreur lors de l'invalidation du refresh token: {str(e)}")

            # Nettoyer les tokens côté client
            response = Response(
                {'success': True, 'message': 'Déconnexion réussie'}, 
                status=status.HTTP_200_OK
            )
            
            # Supprimer les cookies si présents
            response.delete_cookie('auth_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except Exception as e:
            print(f"Erreur lors de la déconnexion: {str(e)}")
            return Response(
                {'success': True, 'message': 'Déconnexion effectuée'},
                status=status.HTTP_200_OK
            )