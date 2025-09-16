from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
import requests
import jwt
import logging
from .services import KeycloakService

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def keycloak_health_check(request):
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_endpoint(request):
    """
    Endpoint protetto che richiede autenticazione
    """
    return Response({
        "status": "success",
        "message": "Accesso autorizzato!",
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_token(request):
    """
    Endpoint per validare un token JWT di Keycloak
    """
    token = request.data.get('token')
    
    if not token:
        return Response({
            "status": "error",
            "message": "Token mancante"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Rimuovi il prefisso "Bearer " se presente
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Decodifica il token usando PyJWT
        public_key = settings.KEYCLOAK_CONFIG.get('PUBLIC_KEY')
        if not public_key:
            return Response({
                "status": "error",
                "message": "Chiave pubblica non configurata"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        validated_token = jwt.decode(
            token,
            public_key,
            algorithms=settings.KEYCLOAK_CONFIG['ALGORITHMS'],
            audience=settings.KEYCLOAK_CONFIG['AUDIENCE']
        )
        
        # Sincronizza l'utente con Keycloak se necessario
        keycloak_service = KeycloakService()
        user = keycloak_service.sync_user_from_keycloak(validated_token['sub'])
        
        return Response({
            "status": "success",
            "message": "Token valido",
            "token_data": {
                "sub": validated_token.get('sub'),
                "preferred_username": validated_token.get('preferred_username'),
                "email": validated_token.get('email'),
                "exp": validated_token.get('exp'),
                "iat": validated_token.get('iat'),
                "aud": validated_token.get('aud')
            },
            "django_user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Token non valido: {str(e)}"
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def keycloak_config(request):
    """
    Endpoint per visualizzare la configurazione Keycloak (senza segreti)
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


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint per autenticare un utente con Keycloak
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            "status": "error",
            "message": "Username e password sono richiesti"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        keycloak_service = KeycloakService()
        auth_result = keycloak_service.authenticate_user(username, password)
        
        if auth_result['success']:
            # Valida il token per ottenere i dati utente
            token_validation = keycloak_service.validate_token(auth_result['access_token'])
            
            if token_validation['valid']:
                return Response({
                    "status": "success",
                    "message": "Autenticazione riuscita",
                    "tokens": {
                        "access_token": auth_result['access_token'],
                        "refresh_token": auth_result['refresh_token'],
                        "expires_in": auth_result['expires_in'],
                        "token_type": auth_result['token_type']
                    },
                    "user": token_validation['user_data']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": "Token ricevuto non valido",
                    "details": token_validation
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "status": "error",
                "message": auth_result['message'],
                "error_code": auth_result['error']
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Errore durante l'autenticazione: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_jwt_token(request):
    """
    Endpoint per validare un token JWT e ottenere i dati utente
    """
    token = request.data.get('token')
    
    if not token:
        return Response({
            "status": "error",
            "message": "Token richiesto"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Rimuovi il prefisso "Bearer " se presente
    if token.startswith('Bearer '):
        token = token[7:]
    
    try:
        keycloak_service = KeycloakService()
        validation_result = keycloak_service.validate_token(token)
        
        if validation_result['valid']:
            return Response({
                "status": "success",
                "message": "Token valido",
                "user": validation_result['user_data'],
                "token_info": {
                    "expires_at": validation_result['token_data'].get('exp'),
                    "issued_at": validation_result['token_data'].get('iat'),
                    "issuer": validation_result['token_data'].get('iss')
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": validation_result['message'],
                "error_code": validation_result['error']
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Errore durante la validazione: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Endpoint per registrare un nuovo utente in Keycloak e Django
    """
    required_fields = ['username', 'email', 'password']
    user_data = {}
    
    # Validazione campi obbligatori
    for field in required_fields:
        value = request.data.get(field)
        if not value:
            return Response({
                "status": "error",
                "message": f"Il campo '{field}' è obbligatorio"
            }, status=status.HTTP_400_BAD_REQUEST)
        user_data[field] = value
    
    # Campi opzionali
    user_data['first_name'] = request.data.get('first_name', '')
    user_data['last_name'] = request.data.get('last_name', '')
    
    # Validazione email
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    
    try:
        validate_email(user_data['email'])
    except ValidationError:
        return Response({
            "status": "error",
            "message": "Email non valida"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validazione password (minimo 8 caratteri)
    if len(user_data['password']) < 8:
        return Response({
            "status": "error",
            "message": "La password deve essere di almeno 8 caratteri"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verifica se l'utente esiste già in Django
    if User.objects.filter(email=user_data['email']).exists():
        return Response({
            "status": "error",
            "message": "Email già registrata"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=user_data['username']).exists():
        return Response({
            "status": "error",
            "message": "Username già in uso"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        keycloak_service = KeycloakService()
        result = keycloak_service.create_user(user_data)
        
        if result['success']:
            return Response({
                "status": "success",
                "message": "Utente registrato con successo",
                "user": {
                    "id": result['django_user'].id,
                    "keycloak_id": result['keycloak_id'],
                    "username": result['django_user'].username,
                    "email": result['django_user'].email,
                    "first_name": result['django_user'].first_name,
                    "last_name": result['django_user'].last_name
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "error",
                "message": result['message'],
                "error_code": result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            "status": "error",
            "message": "Errore interno del server"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)