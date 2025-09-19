from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import jwt
import logging

from ..services import KeycloakService


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint per autenticare un utente con Keycloak.
    
    Parametri richiesti:
    - username: Nome utente o email
    - password: Password dell'utente
    
    Restituisce:
    - access_token: Token JWT per l'accesso alle API
    - refresh_token: Token per rinnovare l'access_token
    - user: Dati dell'utente autenticato
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
        logging.getLogger(__name__).error(f"Login error: {str(e)}")
        return Response({
            "status": "error",
            "message": f"Errore durante l'autenticazione: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_jwt_token(request):
    """
    Endpoint per validare un token JWT e ottenere i dati utente (versione migliorata).
    
    Parametri richiesti:
    - token: Token JWT da validare
    
    Restituisce:
    - user: Dati dell'utente
    - token_info: Informazioni sul token (scadenza, emissione, etc.)
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
        logging.getLogger(__name__).error(f"JWT validation error: {str(e)}")
        return Response({
            "status": "error",
            "message": f"Errore durante la validazione: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)