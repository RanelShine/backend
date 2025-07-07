#accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from communes.models import Commune



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'nom', 'prenom', 'telephone', 'role', 'commune', 'is_active', 'is_verified']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    commune = serializers.PrimaryKeyRelatedField(queryset=Commune.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['email', 'nom', 'prenom', 'telephone', 'role', 'commune', 'password']
        
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            nom=validated_data['nom'],
            prenom=validated_data['prenom'],
            telephone=validated_data.get('telephone', ''),
            role=validated_data.get('role', 'Citoyens'),
            commune=validated_data.get('commune'),
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Identifiants incorrects. Veuillez réessayer.')
            
            if not user.is_active:
                raise serializers.ValidationError('Ce compte n\'est pas actif. Veuillez vérifier votre email.')
        else:
            raise serializers.ValidationError('Veuillez fournir à la fois email et mot de passe.')
        
        data['user'] = user
        return data
#     from accounts.models import User
# user = User.objects.get(email="ranelleshine076@gmail.com")
# user.is_active = True
# user.is_verified = True  
# user.save()
