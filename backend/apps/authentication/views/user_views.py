from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging
from drf_spectacular.utils import extend_schema

from ..services import KeycloakService

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'email': {'type': 'string'},
                'password': {'type': 'string'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'}
            },
            'required': ['username', 'email', 'password']
        }
    },
    responses={201: {'description': 'User registered successfully'}},
    description='Register a new user in Keycloak and Django'
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
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