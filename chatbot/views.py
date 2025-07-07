# chatbot/views.py

import os
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from google.generativeai import GenerativeModel, configure
import base64

# Configure Gemini API avec la clé API
# La clé sera chargée depuis les settings de Django, qui eux-mêmes lisent le .env
configure(api_key=os.getenv("GEMINI_API_KEY"))

@csrf_exempt
def chat_gemini(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Seules les requêtes POST sont autorisées.")

    try:
        body = json.loads(request.body)
        message = body.get('message')
        attachments = body.get('attachments', [])
        history = body.get('history', [])

        if not message:
            return HttpResponseBadRequest("Le champ 'message' est requis.")

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Requête invalide. Le corps de la requête doit être un JSON valide.")
    except Exception as e:
        return HttpResponseBadRequest(f"Erreur lors de l'analyse du corps de la requête : {str(e)}")

    try:
        model = GenerativeModel(model_name="gemini-1.5-flash")

        system_prompt = """
Tu es un assistant virtuel expert spécialisé en redevabilité verte, climato-résilience et développement durable, conçu par le CIPCRE (Centre International de Promotion de la Création et de la Recherche Environnementale).

IDENTITÉ ET RÔLE :
- Tu es un assistant virtuel textuel conçu par le CIPCRE
- Tu es là pour toutes les préoccupations en rapport avec la redevabilité verte, la climato-résilience et le développement durable
- Tu réponds uniquement aux questions liées à ces domaines

DOMAINES D'EXPERTISE :
- Redevabilité verte et transparence environnementale
- Climato-résilience et adaptation au changement climatique
- Développement durable et objectifs de développement durable (ODD)
- Reporting environnemental et social (ESG)
- Économie circulaire et gestion des ressources
- Énergies renouvelables et transition énergétique
- Biodiversité et conservation
- Agriculture durable et sécurité alimentaire
- Gestion des risques climatiques
- Politiques environnementales et gouvernance
- Finance verte et investissements durables
- Innovation technologique pour l'environnement

INSTRUCTIONS DE RÉPONSE :
1. Si on te demande qui tu es, réponds : "Je suis un assistant virtuel textuel conçu par le CIPCRE et je suis là pour toutes vos préoccupations en rapport avec la redevabilité verte, la climato-résilience et le développement durable."

2. Réponds UNIQUEMENT aux questions liées à tes domaines d'expertise. Si une question sort de ces domaines, réponds poliment que tu ne peux traiter que les sujets liés à la redevabilité verte et à la climato-résilience.

3. Fournis des réponses détaillées, pratiques et basées sur les meilleures pratiques internationales.

4. Utilise un ton professionnel mais accessible, adapté au contexte francophone.

5. Propose des solutions concrètes et des recommandations actionnables.

6. Cite des exemples pertinents quand c'est approprié.

7. Encourage les pratiques durables et responsables.

CONTEXTE GÉOGRAPHIQUE :
Adapte tes réponses au contexte africain et francophone quand c'est pertinent, en tenant compte des spécificités locales.
        """

        # Build conversation context for Gemini
        chat_parts = [{"text": system_prompt}]

        # Add recent history for context
        if history:
            recent_history = history[-6:]  # Last 6 messages
            for msg in recent_history:
                role = "user" if msg['isUser'] else "model"
                chat_parts.append({"text": f"{role}: {msg['content']}"})

        # Add current message
        chat_parts.append({"text": f"user: {message}"})

        # Handle attachments if present
        if attachments:
            for attachment in attachments:
                if attachment.get('type', '').startswith('image/') and attachment.get('base64'):
                    try:
                        # Decode base64 string
                        image_data = base64.b64decode(attachment['base64'])
                        # Append image data to parts
                        chat_parts.append({
                            "mime_type": attachment['type'],
                            "data": image_data
                        })
                    except Exception as e:
                        print(f"Erreur lors du décodage de l'image Base64 : {e}")
                        # Optionally, return an error or skip the attachment
                        continue

        # The Gemini API expects an array of parts for content
        # For a simple chat, we concatenate text parts if no images, otherwise pass them as separate parts
        final_parts = []
        current_text_part = ""

        for part in chat_parts:
            if "text" in part:
                current_text_part += part["text"] + "\n"
            elif "mime_type" in part:
                if current_text_part:
                    final_parts.append(current_text_part)
                    current_text_part = ""
                final_parts.append({"mime_type": part["mime_type"], "data": part["data"]})

        if current_text_part:
            final_parts.append(current_text_part)

        # Call Gemini API
        # If there are image attachments, the model.generate_content expects a list of parts directly
        # Otherwise, for pure text, it can take a single string or a list of strings
        if any("mime_type" in p for p in final_parts):
            # If images are present, we send the list of mixed content
            gemini_response = model.generate_content(final_parts)
        else:
            # If only text, we can send the concatenated string
            gemini_response = model.generate_content(final_parts[0]) # Assuming all text parts were concatenated into the first element

        response_text = gemini_response.text

        return JsonResponse({'message': response_text})

    except Exception as e:
        print(f"Erreur API Chat Gemini: {e}")
        error_message = 'Désolé, une erreur est survenue. Veuillez réessayer dans quelques instants.'
        if "API key" in str(e):
            error_message = 'Configuration API manquante. Veuillez configurer votre clé Gemini.'
        return HttpResponseServerError(error_message)