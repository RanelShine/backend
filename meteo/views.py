# meteo/views.py

import os
import json
import requests
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings # Pour accéder aux clés API

# Importer la bibliothèque Google Generative AI pour Python
# Assurez-vous d'avoir installé: pip install google-generativeai
import google.generativeai as genai

# Configurez la clé API Gemini une fois au démarrage de l'application
# ou au moins avant d'appeler le modèle.
# C'est mieux de le faire ici car cette application gère Gemini aussi.
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("ATTENTION: Clé GEMINI_API_KEY non configurée dans les paramètres Django.")

# --- API MÉTÉO (weather.get.ts) ---
@csrf_exempt
def get_weather(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Méthode non autorisée. Seule la méthode GET est acceptée.")

    lat = request.GET.get('lat', '48.8566')  # Paris par défaut
    lon = request.GET.get('lon', '2.3522')

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return HttpResponseServerError("Clé API OpenWeather manquante dans la configuration du serveur.")

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"
        print(f"Weather API - URL: {url.replace(api_key, 'API_KEY_HIDDEN')}") # Masque la clé pour les logs

        response = requests.get(url)
        response.raise_for_status()  # Lance une exception pour les codes d'état HTTP 4xx/5xx
        data = response.json()
        print("Weather API - Success")

        # Récupérer aussi les données horaires (forecast)
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"
        forecast_response = requests.get(forecast_url)
        
        hourly_data = []
        if forecast_response.ok:
            forecast_data = forecast_response.json()
            # Prend les 12 prochaines heures de prévisions
            hourly_data = [
                {
                    "dt": item["dt"] * 1000, # Convertir en millisecondes pour compatibilité JS
                    "temp": item["main"]["temp"],
                    "weather": item["weather"]
                }
                for item in forecast_data["list"][:12]
            ]
        
        return JsonResponse({
            "data": {
                "current": {
                    "temp": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"] * 3.6, # Convertir m/s en km/h
                    "weather": data["weather"]
                },
                "hourly": hourly_data
            }
        })

    except requests.exceptions.RequestException as e:
        print(f"Weather API Error: {e}")
        return HttpResponseServerError(f"Erreur météo: Impossible de joindre l'API OpenWeather. {e}")
    except KeyError as e:
        print(f"Weather API Parsing Error: Missing key in response - {e}")
        return HttpResponseServerError("Erreur météo: Format de réponse inattendu de l'API OpenWeather.")
    except Exception as e:
        print(f"Weather API Unexpected Error: {e}")
        return HttpResponseServerError(f"Erreur météo inattendue: {e}")

# --- API POLLUTION (pollution.get.ts) ---
@csrf_exempt
def get_pollution(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Méthode non autorisée. Seule la méthode GET est acceptée.")

    lat = request.GET.get('lat', '48.8566')  # Paris par défaut
    lon = request.GET.get('lon', '2.3522')

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return HttpResponseServerError("Clé API OpenWeather manquante dans la configuration du serveur.")

    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        print(f"Pollution API - URL: {url.replace(api_key, 'API_KEY_HIDDEN')}") # Masque la clé pour les logs

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print("Pollution API - Success")
        
        return JsonResponse(data) # Retourne les données brutes de pollution

    except requests.exceptions.RequestException as e:
        print(f"Pollution API Error: {e}")
        return HttpResponseServerError(f"Erreur pollution: Impossible de joindre l'API OpenWeather. {e}")
    except KeyError as e:
        print(f"Pollution API Parsing Error: Missing key in response - {e}")
        return HttpResponseServerError("Erreur pollution: Format de réponse inattendu de l'API OpenWeather.")
    except Exception as e:
        print(f"Pollution API Unexpected Error: {e}")
        return HttpResponseServerError(f"Erreur pollution inattendue: {e}")

# --- API RECOMMANDATIONS (recommandations.post.ts) ---
@csrf_exempt

def get_recommendations(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Méthode non autorisée. Seule la méthode POST est acceptée.")

    try:
        body = json.loads(request.body)
        type = body.get('type')
        weather_data = body.get('weatherData')
        pollution_data = body.get('pollutionData')

        if not type:
            return HttpResponseBadRequest("Le champ 'type' est requis dans le corps de la requête.")
        
        # Le modèle est initialisé ici car il dépend de la clé GEMINI_API_KEY des settings
        model = genai.GenerativeModel(model_name="gemini-1.5-flash") 

        prompt = ''
        if type == 'agricultural':
            if not weather_data:
                return HttpResponseBadRequest("Les données météorologiques ('weatherData') sont requises pour les recommandations agricoles.")
            
            # Utilisation de .get() avec valeurs par défaut pour éviter les KeyErrors si les clés sont manquantes
            temp = weather_data.get('current', {}).get('temp', 'N/A')
            humidity = weather_data.get('current', {}).get('humidity', 'N/A')
            wind_speed = round(weather_data.get('current', {}).get('wind_speed', 0)) # Arrondi
            weather_desc = weather_data.get('current', {}).get('weather', [{}])[0].get('description', 'inconnu')

            prompt = f"""
En tant qu'expert en agriculture durable et climato-résilience, génère 4 recommandations pratiques pour les agriculteurs basées sur ces conditions météorologiques :
- Température: {temp}°C
- Humidité: {humidity}%
- Vitesse du vent: {wind_speed} km/h
- Conditions: {weather_desc}

Les recommandations doivent être :
- Courtes et actionables (maximum 15 mots chacune)
- Adaptées aux conditions actuelles
- Axées sur la durabilité et l'adaptation climatique
- Pratiques pour les agriculteurs camerounais

Réponds uniquement avec 4 recommandations séparées par des retours à la ligne, sans numérotation ni puces.
"""
        elif type == 'pollution':
            if not pollution_data:
                return HttpResponseBadRequest("Les données de pollution ('pollutionData') sont requises pour les recommandations de pollution.")
            
            # Utilisation de .get() avec valeurs par défaut et gestion des listes/dictionnaires imbriqués
            aqi = pollution_data.get('list', [{}])[0].get('main', {}).get('aqi', 'N/A')
            # Utilisez float(value) si les données peuvent être des nombres
            pm25 = pollution_data.get('list', [{}])[0].get('components', {}).get('pm2_5', 'N/A')
            pm10 = pollution_data.get('list', [{}])[0].get('components', {}).get('pm10', 'N/A')

            prompt = f"""
En tant qu'expert en santé environnementale, génère 4 recommandations pratiques basées sur cet indice de pollution :
- Indice de qualité de l'air: {aqi}/5
- PM2.5: {float(pm25):.1f} μg/m³
- PM10: {float(pm10):.1f} μg/m³

Les recommandations doivent être :
- Courtes et actionables (maximum 15 mots chacune)
- Adaptées au niveau de pollution actuel
- Axées sur la protection de la santé et de l'environnement
- Pratiques pour le grand public camerounais

Réponds uniquement avec 4 recommandations séparées par des retours à la ligne, sans numérotation ni puces.
"""
        else:
            return HttpResponseBadRequest("Type de recommandation non valide. 'agricultural' ou 'pollution' sont acceptés.")

        if not prompt: # Au cas où le type est invalide mais le contrôle initial est passé
             return HttpResponseBadRequest("Impossible de générer le prompt. Type de recommandation ou données manquantes/incorrectes.")

        print(f"Gemini Recommendations Prompt:\n{prompt}")
        response_gemini = model.generate_content(prompt)
        text_response = response_gemini.text
        
        recommendations = [rec.strip() for rec in text_response.strip().split('\n') if rec.strip()]
        
        return JsonResponse({"recommendations": recommendations})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Requête invalide. Le corps de la requête doit être un JSON valide.")
    except genai.APIError as e:
        print(f"Gemini API Error (Recommendations): {e}")
        return HttpResponseServerError(f"Erreur lors de la communication avec l'API Gemini pour les recommandations: {e}")
    except Exception as e:
        print(f"Recommendations Unexpected Error: {e}")
        return HttpResponseServerError(f"Erreur inattendue lors de la génération des recommandations: {e}")

# --- API ÉDUCATIONNELLE (educational.get.ts) ---
@csrf_exempt
def get_educational_message(request):
    if request.method != 'GET':
        return HttpResponseBadRequest("Méthode non autorisée. Seule la méthode GET est acceptée.")

    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        prompt = """
En tant qu'expert en climato-résilience et développement durable, génère un message éducatif unique qui commence par "Saviez-vous que" et qui porte sur :
- L'adaptation au changement climatique
- Les pratiques agricoles durables
- La protection de l'environnement
- La biodiversité
- Les solutions basées sur la nature
- L'économie circulaire
- Les énergies renouvelables
 
Le message doit :
- Commencer obligatoirement par "Saviez-vous que"
- Être informatif et surprenant
- Contenir des données chiffrées précises
- Être inspirant et encourager l'action
- Faire maximum 2 phrases
- Être adapté au contexte camerounais
 
Réponds uniquement avec le message, sans guillemets ni formatage supplémentaire.
"""
        print(f"Gemini Educational Prompt:\n{prompt}")
        response_gemini = model.generate_content(prompt)
        message = response_gemini.text.strip()
        
        return JsonResponse({"message": message})

    except genai.APIError as e:
        print(f"Gemini API Error (Educational): {e}")
        return HttpResponseServerError(f"Erreur lors de la communication avec l'API Gemini pour le message éducatif: {e}")
    except Exception as e:
        print(f"Educational Unexpected Error: {e}")
        return HttpResponseServerError(f"Erreur inattendue lors de la génération du message éducatif: {e}")