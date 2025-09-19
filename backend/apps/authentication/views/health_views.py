from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
import logging
from drf_spectacular.utils import extend_schema

from ..services import KeycloakService


@extend_schema(
    responses={200: {'description': 'Keycloak health status'}},
    description='Check Keycloak server health and connection'
)
@api_view(['GET'])
@permission_classes([AllowAny])
def keycloak_health_check(request):
    """
    Endpoint per verificare lo stato di salute della connessione con Keycloak.
    Testa la connessione al server, l'accesso al realm e la chiave pubblica.
    """
    logger = logging.getLogger(__name__)
    
    try:
        server_url = settings.KEYCLOAK_CONFIG['SERVER_URL']
        realm = settings.KEYCLOAK_CONFIG['REALM']
        verify_ssl = settings.KEYCLOAK_CONFIG['VERIFY_SSL']
        
        logger.info(f"Server URL: {server_url}")
        logger.info(f"Realm: {realm}")
        logger.info(f"Verify SSL: {verify_ssl}")
        
        # Test 1: Connessione al server base
        try:
            logger.info(f"Testing base server connection...")
            base_response = requests.get(server_url, timeout=10, verify=verify_ssl)
            logger.info(f"Base server response: {base_response.status_code}")
        except Exception as e:
            logger.error(f"Base server connection failed: {str(e)}")
        
        # Test 2: Endpoint del realm
        config_url = f"{server_url}/realms/{realm}"
        logger.info(f"Testing realm endpoint: {config_url}")
        
        try:
            response = requests.get(config_url, timeout=10, verify=verify_ssl)
            logger.info(f"Realm endpoint response: {response.status_code}")
            
            if response.status_code == 404:
                logger.error(f"Realm '{realm}' not found!")
                return Response({
                    "status": "error",
                    "message": f"Realm '{realm}' non trovato sul server Keycloak",
                    "details": {
                        "server_url": server_url,
                        "realm": realm,
                        "config_url": config_url,
                        "status_code": response.status_code
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            if response.status_code == 200:
                config_data = response.json()
                logger.info(f"Realm config retrieved successfully")
                
                # Test 3: Verifica chiave pubblica
                try:
                    keycloak_service = KeycloakService()
                    public_key = keycloak_service.get_public_key()
                    public_key_status = "✅ Ottenuta con successo"
                    logger.info(f"Public key retrieved successfully")
                except Exception as e:
                    public_key_status = f"❌ Errore: {str(e)}"
                    logger.error(f"Public key error: {str(e)}")
                
                return Response({
                    "status": "success",
                    "message": "Connessione con Keycloak funzionante",
                    "details": {
                        "server_url": server_url,
                        "realm": realm,
                        "client_id": settings.KEYCLOAK_CONFIG['CLIENT_ID'],
                        "issuer": config_data.get('issuer'),
                        "authorization_endpoint": config_data.get('authorization_endpoint'),
                        "token_endpoint": config_data.get('token_endpoint'),
                        "userinfo_endpoint": config_data.get('userinfo_endpoint'),
                        "public_key_status": public_key_status,
                        "ssl_verification": verify_ssl
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Unexpected status code: {response.status_code}")
                return Response({
                    "status": "error",
                    "message": f"Risposta inaspettata da Keycloak: {response.status_code}",
                    "details": {
                        "server_url": server_url,
                        "realm": realm,
                        "config_url": config_url,
                        "status_code": response.status_code,
                        "response_text": response.text[:500]
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Errore SSL: {str(e)}",
                "suggestion": "Prova a disabilitare la verifica SSL con KEYCLOAK_VERIFY_SSL=false"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Errore di connessione: {str(e)}",
                "details": {
                    "server_url": server_url,
                    "suggestion": "Verifica che il server Keycloak sia raggiungibile"
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout Error: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Timeout della connessione: {str(e)}"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Generic Error: {str(e)}")
        return Response({
            "status": "error",
            "message": f"Errore generico: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: {'description': 'Keycloak configuration'}},
    description='Get Keycloak configuration for frontend'
)
@api_view(['GET'])
@permission_classes([AllowAny])
def keycloak_config(request):
    """
    Endpoint per visualizzare la configurazione Keycloak (senza segreti).
    Fornisce le informazioni necessarie per il frontend.
    """
    config = settings.KEYCLOAK_CONFIG.copy()
    # Rimuovi il client secret per sicurezza
    config.pop('CLIENT_SECRET', None)
    
    return Response({
        "status": "success",
        "keycloak_config": config,
        "frontend_config": {
            "auth_url": f"{config['SERVER_URL']}/realms/{config['REALM']}/protocol/openid-connect/auth",
            "token_url": f"{config['SERVER_URL']}/realms/{config['REALM']}/protocol/openid-connect/token",
            "userinfo_url": f"{config['SERVER_URL']}/realms/{config['REALM']}/protocol/openid-connect/userinfo",
            "logout_url": f"{config['SERVER_URL']}/realms/{config['REALM']}/protocol/openid-connect/logout"
        }
    }, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: {'description': 'Protected content access'}},
    description='Test endpoint for authenticated users'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_endpoint(request):
    return Response({
        "status": "success",
        "message": "Accesso autorizzato!",
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email
        }
    }, status=status.HTTP_200_OK)