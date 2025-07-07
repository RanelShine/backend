# accounts/utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(email: str, code: str):
    subject = "Activation de votre compte"
    message = (
        f"Merci de vous être inscrit.\n\n"
        f"Votre code de vérification à 6 chiffres : {code}\n\n"
        "Ce code expirera dans 1 heure.\n\n"
        "Si vous n’avez pas demandé cet email, ignorez-le."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
