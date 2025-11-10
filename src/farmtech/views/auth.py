import logging
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()

class KeycloakAuthAPIView(APIView):
    
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"error": "Username e password sono obbligatori"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        keycloak_config = getattr(settings, 'SOCIALACCOUNT_PROVIDERS_DEFS', {}).get('keycloak', {})
        
        if not keycloak_config:
            keycloak_config = getattr(settings, '_KEYCLOAK_SOCIALACCOUNT_PROVIDER', {})
        
        token_url = keycloak_config.get('ACCESS_TOKEN_URL')
        userinfo_url = keycloak_config.get('PROFILE_URL')
        keycloak_client_id = keycloak_config.get('CLIENT_ID')
        keycloak_client_secret = keycloak_config.get('SECRET')
        verify_ssl = keycloak_config.get('VERIFY_SSL', True)
        
        if not all([token_url, userinfo_url, keycloak_client_id]):
            return Response(
                {
                    "error": "Configurazione Keycloak mancante",
                    "debug": {
                        "token_url": token_url,
                        "userinfo_url": userinfo_url,
                        "client_id": keycloak_client_id,
                        "has_secret": bool(keycloak_client_secret)
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        token_data = {
            'grant_type': 'password',
            'client_id': keycloak_client_id,
            'username': username,
            'password': password,
        }
        
        if keycloak_client_secret:
            token_data['client_secret'] = keycloak_client_secret
        
        try:
            token_response = requests.post(
                token_url,
                data=token_data,
                verify=verify_ssl
            )
            
            if token_response.status_code != 200:
                logger.error(f"Keycloak auth failed: {token_response.text}")
                return Response(
                    {"error": "Credenziali non valide"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            keycloak_tokens = token_response.json()
            access_token = keycloak_tokens.get('access_token')
            
            userinfo_response = requests.get(
                userinfo_url,
                headers={'Authorization': f'Bearer {access_token}'},
                verify=verify_ssl
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"Keycloak userinfo failed: {userinfo_response.text}")
                return Response(
                    {"error": "Errore recupero informazioni utente"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            userinfo = userinfo_response.json()
            
            keycloak_username = userinfo.get('preferred_username', username)
            email = userinfo.get('email', '')
            first_name = userinfo.get('given_name', '')
            last_name = userinfo.get('family_name', '')
            
            user, created = User.objects.get_or_create(
                username=keycloak_username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            if not created:
                if email:
                    user.email = email
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                user.save()
            
            django_token, token_created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': django_token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'keycloak_access_token': access_token,
                'keycloak_refresh_token': keycloak_tokens.get('refresh_token'),
                'expires_in': keycloak_tokens.get('expires_in')
            }, status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Errore connessione Keycloak: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Errore connessione con Keycloak: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Errore autenticazione Keycloak: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Errore durante l'autenticazione: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
