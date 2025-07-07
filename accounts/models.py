#accounts/models.py
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from communes.models import Commune


class UserManager(BaseUserManager):
    #classe permettant de créer un utilisateur avec une adresse email
    #fonction pour créer un utilisateur
    # **extra_fields pour des champs supplementaires comme le nom, prénom, etc.
    def create_user(self, email, password=None, **extra_fields):
        #si l'email n'est pas fourni, une erreur est levée
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        #unifier(normaliser) toute les variations de l'email pour eviter les erreurs liées à la casse
        #en utilisant la fonction normalize_email de django
        email = self.normalize_email(email)
        #créer un utilisateur avec l'email et le mot de passe hashé
        #et les champs supplémentaires fournis
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        #enregistre les onnées dans la base de données
        user.save(using=self._db)
        return user
# fonction de la classe UserManager pour créer un super utilisateur
    def create_superuser(self, email, password=None, **extra_fields):
        #is_staff definit si l'utilisateur peut se connecter à l'interface d'administration
        extra_fields.setdefault('is_staff', True)
        #is_superuser definit si l'utilisateur a tous les droits
        extra_fields.setdefault('is_superuser', True)
        #is_active definit si l'utilisateur est actif et peut se connecter
        extra_fields.setdefault('is_active', True)
        #role defint l'utilisateur comme superadmin
        extra_fields.setdefault('role', 'Administrateur')
        #lever une erreur si l'utilisateur n'as pas is_staff et is_superuser a true
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

#classe User qui hérite de AbstractBaseUser et PermissionsMixin
#AbstractBaseUser fournit les fonctionnalités de base pour l'authentification
class User(AbstractBaseUser, PermissionsMixin):
    #definition des roles pour le select du role lors de l'inscription
    ROLE_CHOICES = (
        ('Citoyens', 'Citoyens'),
        ('ONG', 'ONG'),
        ('Entreprise', 'Entreprise'),
        ('ctd', 'CTD'),
    )
    
    #definition des champs requis pour l'inscription de l'utilisateur
    email = models.EmailField(_('adresse email'), unique=True)
    nom = models.CharField(_('nom'), max_length=150)
    prenom = models.CharField(_('prénom'), max_length=150)
    telephone = models.CharField(_('téléphone'), max_length=15, blank=True)
    role = models.CharField(_('rôle'), max_length=15, choices=ROLE_CHOICES, default='Citoyens')
    commune = models.ForeignKey('communes.Commune', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    #code de vérification pour l'activation du comptete
    verification_code   = models.CharField(max_length=6, null=True, blank=True)
    #date d'expiration du code de vérification
    #is_verified pour savoir si l'utilisateur a vérifié son compte
    code_expiration     = models.DateTimeField(null=True, blank=True)
    is_verified         = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #la classe UserManager est utilisée pour gérer les utilisateurs
    #creation d'un objet UserManager
    objects = UserManager()
    
    #le champ email est utilisé comme identifiant unique pour l'authentification
    USERNAME_FIELD = 'email'
    #autres champs requis pour la création d'un utilisateur
    REQUIRED_FIELDS = ['nom', 'prenom', 'telephone', 'role', 'commune']

#fonction pour définir le code de vérification aleaotire a 6 chiffres
    def set_verification_code(self):
        import random, string
        code = ''.join(random.choices(string.digits, k=6))
        self.verification_code = code
        self.code_expiration   = timezone.now() + timedelta(hours=1)
        self.is_active         = False
        self.is_verified       = False
        self.save()
        return code
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        
    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.email})"
        
    def get_full_name(self):
        
        return f"{self.nom} {self.prenom}"
    
    def get_short_name(self):
        return self.nom