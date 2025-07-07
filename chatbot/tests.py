from chatbot_logic import my_chat
from PIL import Image

# Test avec texte seulement
reponse_texte = my_chat("Quels sont les avantages de la préparation des repas à l'avance ?")
print("Réponse texte uniquement :")
print(reponse_texte)
print("\n" + "="*50 + "\n")

# Test avec image et texte
try:
    with Image.open("repas_prepare.png") as img:
        reponse_image = my_chat(
            "qu'est ce que tu vois sur l'image",
            img
        )
    print("Réponse image et texte :")
    print(reponse_image)
except FileNotFoundError:
    print("Fichier image non trouvé. Assurez-vous que 'repas_prepare.jpg' existe dans le même répertoire.")