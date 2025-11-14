# file: copernicus_api.py

import logging
from typing import Dict, Any
import requests
from django.conf import settings
from django.core.cache import cache

from farmtech.exceptions import CopernicusAPIError


# Configura un logger per il debug
logger = logging.getLogger(__name__)

# --- Cache key per il token ---
TOKEN_CACHE_KEY = 'copernicus_auth_token'

def get_auth_token() -> str:
    """
    Ottiene un token di autenticazione da Copernicus.
    Utilizza la cache di Django per evitare richieste ripetute.
    """
    # 1. Controlla se il token è già in cache
    token = cache.get(TOKEN_CACHE_KEY)
    if token:
        logger.info("Token di Copernicus recuperato dalla cache.")
        return token

    # 2. Se non è in cache, richiedine uno nuovo
    logger.info("Richiesta di un nuovo token di autenticazione a Copernicus.")
    payload = {
        'grant_type': 'client_credentials',
        'client_id': settings.COPERNICUS_CLIENT_ID,
        'client_secret': settings.COPERNICUS_CLIENT_SECRET,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(settings.COPERNICUS_AUTH_URL, data=payload, headers=headers)
        response.raise_for_status()  # Solleva un'eccezione per errori HTTP (es. 4xx, 5xx)
        
        data = response.json()
        new_token = data.get('access_token')
        expires_in = data.get('expires_in', 3600)  # Durata in secondi

        if not new_token:
            raise ValueError("La risposta dell'API non conteneva un access_token.")

        # 3. Salva il nuovo token nella cache con una scadenza
        # (sottraiamo 60 secondi per sicurezza)
        cache.set(TOKEN_CACHE_KEY, new_token, timeout=expires_in - 60)
        logger.info("Nuovo token di Copernicus salvato in cache.")
        
        return new_token

    except requests.exceptions.RequestException as e:
        logger.error(f"Errore durante la richiesta del token a Copernicus: {e}")
        raise  # Rilancia l'eccezione per gestirla nella view


def get_tiff_from_copernicus(
    geometry: Dict[str, Any],
    token: str,
    start_date: str = None,
    end_date: str = None
) -> bytes:
    """
    Richiede un'immagine TIFF a Copernicus basata su una geometria.
    Restituisce i dati binari dell'immagine.

    Args:
        geometry: Geometria GeoJSON del poligono
        token: Token di autenticazione Copernicus
        start_date: Data inizio in formato YYYY-MM-DD (opzionale)
        end_date: Data fine in formato YYYY-MM-DD (opzionale)
    """
    
    # Converti le date in formato ISO con timezone UTC
    start_datetime = f"{start_date}T00:00:00Z"
    end_datetime = f"{end_date}T23:59:59Z"

    # Per semplicità, usiamo la configurazione S2L2A come default
    evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B02", "B03", "B04","B08","B11"],
            output: { bands: 5, sampleType: "AUTO" }
          };
        }
        function evaluatePixel(sample) {
          return [sample.B02, sample.B03, sample.B04, sample.B11, sample.B08];
        }
    """

    request_body = {
        "input": {
            "bounds": {
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                "geometry": geometry
            },
            "data": [{
                "type": "S2L2A",
                "dataFilter": {
                    "timeRange": {
                        "from": start_datetime,
                        "to": end_datetime
                    },
                    "mosaickingOrder": "mostRecent",
                    "maxCloudCoverage": 20
                },
                "processing":{
                    "downsampling":"NEAREST",
                    "upsamplign":"BICUBIC"
                }
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
        },
        "evalscript": evalscript
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'image/tiff',
        'Authorization': f'Bearer {token}',
    }

    try:
        logger.info("Invio richiesta per immagine TIFF a Copernicus.")
        response = requests.post(settings.COPERNICUS_API_URL, json=request_body, headers=headers)
        response.raise_for_status()
        logger.info("Immagine TIFF ricevuta con successo.")
        return response.content  # Dati binari dell'immagine

    except requests.exceptions.HTTPError as e:
        raise CopernicusAPIError(f"Error requesting TIFF from Copernicus: {str(e)}") from e
