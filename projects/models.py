# projects/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

class Project(models.Model):
    """
    Modèle pour les projets environnementaux des communes
    """
    STATUS_CHOICES = [
        ('PLANNED', 'Planifié'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('SUSPENDED', 'Suspendu'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="Titre du projet"
    )
    description = models.TextField(
        verbose_name="Description détaillée"
    )
    commune = models.ForeignKey(
        'communes.Commune', # Assurez-vous que l'application 'communes' est dans INSTALLED_APPS
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name="Commune"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        verbose_name="État du projet"
    )
    start_date = models.DateField(
        verbose_name="Date de début",
        null=True,
        blank=True
    )
    end_date = models.DateField(
        verbose_name="Date de fin prévue",
        null=True,
        blank=True
    )
    budget = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="Budget alloué",
        null=True,
        blank=True
    )
    avancement = models.PositiveIntegerField(
        verbose_name="Avancement (%)",
        default=0,
        help_text="Pourcentage d'avancement du projet (0–100)."
    )
    file = models.FileField(
        upload_to='projects/files/',
        verbose_name="Fichier du projet (image, PDF, doc, ppt, etc.)",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
        verbose_name="Créé par"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Projet"
        verbose_name_plural = "Projets"

    def __str__(self):
        return f"{self.title} ({self.commune.nom})"


class Comment(models.Model):
    """
    Modèle pour représenter un commentaire sur un projet.
    """
    project = models.ForeignKey(
        Project, # Référence directe au modèle Project défini ci-dessus
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Projet"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Référence au modèle d'utilisateur configuré dans settings.py
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Auteur"
    )
    text = models.TextField(
        verbose_name="Commentaire"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Créé le"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Mis à jour le"
    )

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-created_at'] # Trier les commentaires du plus récent au plus ancien

    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.project.title}"


class Accountability(models.Model):
    """
    Modèle pour les demandes de comptes sur les projets
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ANSWERED', 'Répondu'),
        ('CLOSED', 'Clôturé'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='accountability_requests',
        verbose_name="Projet concerné"
    )
    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accountability_requests',
        verbose_name="Citoyen"
    )
    question = models.TextField(
        verbose_name="Question/Demande"
    )
    response = models.TextField(
        verbose_name="Réponse",
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="État de la demande"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de soumission"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='accountability_responses',
        verbose_name="Répondu par"
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de réponse"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande de compte"
        verbose_name_plural = "Demandes de comptes"

    def __str__(self):
        return f"Demande sur « {self.project.title} » par {self.citizen.get_full_name() or self.citizen.email}"

    def save(self, *args, **kwargs):
        if self.response and not self.responded_at:
            self.responded_at = timezone.now()
            self.status = 'ANSWERED'
        super().save(*args, **kwargs)

