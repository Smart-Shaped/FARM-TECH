from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.views import View
import jwt
import requests
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def minio_webhook(request):
	"""Endpoint to receive MinIO event notifications (webhook).

	MinIO posts JSON payloads describing object events. We accept the
	payload, log it for debugging, and return a simple acknowledgement.

	Contract:
	- Input: JSON body (MinIO event format)
	- Output: 200 JSON {"status": "received"} on success
	- Error modes: malformed JSON -> 400
	"""
	logger.info('MinIO webhook called')
	try:
		payload = request.data
		# Log at INFO so production logs keep a record; payload can be large.
		logger.info('MinIO webhook received: %s', payload)

		# TODO: add processing logic (enqueue task, persist event, etc.)

		return Response({"status": "received"}, status=status.HTTP_200_OK)
	except Exception as exc:
		logger.exception('Error handling MinIO webhook')
		return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class MinIOTokenView(View):
    """
    Vista per generare token temporanei per MinIO usando il token Keycloak
    """
    
    def post(self, request):
        try:
            # Estrai il token Keycloak dall'header Authorization
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Token mancante'}, status=401)
            
            keycloak_token = auth_header.split(' ')[1]
            
            # Verifica il token Keycloak
            if not self.verify_keycloak_token(keycloak_token):
                return JsonResponse({'error': 'Token non valido'}, status=401)
            
            # Decodifica il token per ottenere le informazioni utente
            decoded_token = jwt.decode(
                keycloak_token, 
                options={"verify_signature": False}
            )
            
            # Ottieni le credenziali temporanee per MinIO
            minio_credentials = self.get_minio_credentials(decoded_token)
            
            return JsonResponse({
                'accessKey': minio_credentials['accessKey'],
                'secretKey': minio_credentials['secretKey'],
                'sessionToken': minio_credentials.get('sessionToken'),
                'expiration': minio_credentials.get('expiration')
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def verify_keycloak_token(self, token):
        """
        Verifica il token Keycloak con il server
        """
        try:
            # URL dell'endpoint di verifica token di Keycloak
            verify_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(verify_url, headers=headers)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_minio_credentials(self, decoded_token):
        """
        Genera credenziali temporanee per MinIO basate sui claim del token
        """
        # Qui dovresti implementare la logica per ottenere credenziali temporanee
        # usando STS (Security Token Service) di MinIO o una logica personalizzata
        
        # Per ora restituiamo credenziali statiche (da modificare in produzione)
        return {
            'accessKey': 'temp-access-key',
            'secretKey': 'temp-secret-key',
            'sessionToken': 'session-token',
            'expiration': '2024-12-31T23:59:59Z'
        }


class MinIOProxyView(View):
    """
    Vista proxy per le richieste a MinIO che aggiunge automaticamente l'autenticazione
    """
    
    def get(self, request, path):
        return self.proxy_request(request, path, 'GET')
    
    def post(self, request, path):
        return self.proxy_request(request, path, 'POST')
    
    def put(self, request, path):
        return self.proxy_request(request, path, 'PUT')
    
    def delete(self, request, path):
        return self.proxy_request(request, path, 'DELETE')
    
    def proxy_request(self, request, path, method):
        """
        Proxifica le richieste a MinIO aggiungendo l'autenticazione
        """
        # Implementa la logica di proxy con autenticazione automatica
        pass