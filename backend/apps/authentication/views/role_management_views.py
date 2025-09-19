"""
View per la gestione dei ruoli degli utenti in Keycloak.

Queste view permettono agli amministratori di gestire i ruoli degli utenti
direttamente dal backend Django, sincronizzando con Keycloak.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import logging

from ..services import KeycloakService
from ..permissions import AdminOnlyPermission, require_keycloak_role

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated, AdminOnlyPermission])
def get_available_roles(request):
    """
    Ottiene tutti i ruoli disponibili nel realm Keycloak.
    Solo gli admin possono vedere i ruoli disponibili.
    """
    try:
        keycloak_service = KeycloakService()
        result = keycloak_service.get_realm_roles()
        
        if result['success']:
            # Filtra solo i ruoli che ci interessano per evitare ruoli di sistema
            relevant_roles = [
                role for role in result['roles'] 
                if role['name'] in ['admin', 'editor', 'viewer'] or not role['name'].startswith('default-')
            ]
            
            return Response({
                'status': 'success',
                'message': 'Ruoli recuperati con successo',
                'roles': relevant_roles,
                'total_roles': len(relevant_roles)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result['message'],
                'error_code': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error getting available roles: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_roles(request, user_id):
    """
    Ottiene i ruoli di un utente specifico.
    Gli utenti possono vedere i propri ruoli, gli admin possono vedere quelli di tutti.
    """
    try:
        # Trova l'utente
        target_user = get_object_or_404(User, id=user_id)
        
        # Verifica permessi: utente può vedere i propri ruoli, admin può vedere tutti
        if request.user.id != target_user.id and not request.user.keycloak_roles or 'admin' not in request.user.keycloak_roles:
            return Response({
                'status': 'error',
                'message': 'Non hai i permessi per vedere i ruoli di questo utente'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not target_user.keycloak_id:
            return Response({
                'status': 'error',
                'message': 'Utente non collegato a Keycloak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        keycloak_service = KeycloakService()
        result = keycloak_service.get_user_roles(str(target_user.keycloak_id))
        
        if result['success']:
            return Response({
                'status': 'success',
                'message': 'Ruoli utente recuperati con successo',
                'user': {
                    'id': target_user.id,
                    'email': target_user.email,
                    'username': target_user.username,
                    'keycloak_id': str(target_user.keycloak_id)
                },
                'roles': result['roles'],
                'role_names': result['role_names'],
                'django_cached_roles': target_user.keycloak_roles
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result['message'],
                'error_code': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error getting user roles: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, AdminOnlyPermission])
def assign_role_to_user(request):
    """
    Assegna un ruolo a un utente.
    Solo gli admin possono assegnare ruoli.
    
    Body:
    {
        "user_id": 123,
        "role_name": "editor"
    }
    """
    try:
        user_id = request.data.get('user_id')
        role_name = request.data.get('role_name')
        
        if not user_id or not role_name:
            return Response({
                'status': 'error',
                'message': 'user_id e role_name sono richiesti'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trova l'utente
        target_user = get_object_or_404(User, id=user_id)
        
        if not target_user.keycloak_id:
            return Response({
                'status': 'error',
                'message': 'Utente non collegato a Keycloak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica che il ruolo sia valido
        valid_roles = ['admin', 'editor', 'viewer']
        if role_name not in valid_roles:
            return Response({
                'status': 'error',
                'message': f'Ruolo non valido. Ruoli permessi: {", ".join(valid_roles)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        keycloak_service = KeycloakService()
        result = keycloak_service.assign_role_to_user(str(target_user.keycloak_id), role_name)
        
        if result['success']:
            return Response({
                'status': 'success',
                'message': result['message'],
                'user': {
                    'id': target_user.id,
                    'email': target_user.email,
                    'username': target_user.username
                },
                'assigned_role': result['role'],
                'performed_by': request.user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result['message'],
                'error_code': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error assigning role: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, AdminOnlyPermission])
def remove_role_from_user(request):
    """
    Rimuove un ruolo da un utente.
    Solo gli admin possono rimuovere ruoli.
    
    Body:
    {
        "user_id": 123,
        "role_name": "editor"
    }
    """
    try:
        user_id = request.data.get('user_id')
        role_name = request.data.get('role_name')
        
        if not user_id or not role_name:
            return Response({
                'status': 'error',
                'message': 'user_id e role_name sono richiesti'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trova l'utente
        target_user = get_object_or_404(User, id=user_id)
        
        if not target_user.keycloak_id:
            return Response({
                'status': 'error',
                'message': 'Utente non collegato a Keycloak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Protezione: impedisci di rimuovere il ruolo admin dall'ultimo admin
        if role_name == 'admin':
            admin_users = User.objects.filter(keycloak_roles__contains=['admin']).count()
            if admin_users <= 1:
                return Response({
                    'status': 'error',
                    'message': 'Impossibile rimuovere il ruolo admin dall\'ultimo amministratore'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        keycloak_service = KeycloakService()
        result = keycloak_service.remove_role_from_user(str(target_user.keycloak_id), role_name)
        
        if result['success']:
            return Response({
                'status': 'success',
                'message': result['message'],
                'user': {
                    'id': target_user.id,
                    'email': target_user.email,
                    'username': target_user.username
                },
                'removed_role': result['role'],
                'performed_by': request.user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result['message'],
                'error_code': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error removing role: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, AdminOnlyPermission])
def set_user_roles(request):
    """
    Imposta i ruoli di un utente (sostituisce tutti i ruoli esistenti).
    Solo gli admin possono impostare ruoli.
    
    Body:
    {
        "user_id": 123,
        "roles": ["editor", "viewer"]
    }
    """
    try:
        user_id = request.data.get('user_id')
        roles = request.data.get('roles')
        
        if not user_id or roles is None:
            return Response({
                'status': 'error',
                'message': 'user_id e roles sono richiesti'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(roles, list):
            return Response({
                'status': 'error',
                'message': 'roles deve essere una lista'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trova l'utente
        target_user = get_object_or_404(User, id=user_id)
        
        if not target_user.keycloak_id:
            return Response({
                'status': 'error',
                'message': 'Utente non collegato a Keycloak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica che tutti i ruoli siano validi
        valid_roles = ['admin', 'editor', 'viewer']
        invalid_roles = [role for role in roles if role not in valid_roles]
        if invalid_roles:
            return Response({
                'status': 'error',
                'message': f'Ruoli non validi: {", ".join(invalid_roles)}. Ruoli permessi: {", ".join(valid_roles)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Protezione: assicurati che ci sia almeno un admin nel sistema
        if 'admin' not in roles and target_user.keycloak_roles and 'admin' in target_user.keycloak_roles:
            admin_users = User.objects.filter(keycloak_roles__contains=['admin']).exclude(id=target_user.id).count()
            if admin_users == 0:
                return Response({
                    'status': 'error',
                    'message': 'Impossibile rimuovere il ruolo admin dall\'ultimo amministratore'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        keycloak_service = KeycloakService()
        result = keycloak_service.set_user_roles(str(target_user.keycloak_id), roles)
        
        if result['success']:
            return Response({
                'status': 'success',
                'message': result['message'],
                'user': {
                    'id': target_user.id,
                    'email': target_user.email,
                    'username': target_user.username
                },
                'operations': result['operations'],
                'final_roles': result['final_roles'],
                'performed_by': request.user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result['message'],
                'error_code': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error setting user roles: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, AdminOnlyPermission])
def list_users_with_roles(request):
    """
    Lista tutti gli utenti con i loro ruoli.
    Solo gli admin possono vedere questa lista.
    """
    try:
        users = User.objects.filter(keycloak_id__isnull=False).order_by('email')
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'keycloak_id': str(user.keycloak_id),
                'roles': user.keycloak_roles,
                'is_active': user.is_active,
                'last_keycloak_sync': user.last_keycloak_sync
            })
        
        return Response({
            'status': 'success',
            'message': f'Trovati {len(users_data)} utenti',
            'users': users_data,
            'total_users': len(users_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing users with roles: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, AdminOnlyPermission])
def sync_user_roles_from_keycloak(request):
    """
    Sincronizza i ruoli di un utente da Keycloak al database Django.
    Solo gli admin possono sincronizzare ruoli.
    
    Body:
    {
        "user_id": 123
    }
    """
    try:
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'status': 'error',
                'message': 'user_id è richiesto'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Trova l'utente
        target_user = get_object_or_404(User, id=user_id)
        
        if not target_user.keycloak_id:
            return Response({
                'status': 'error',
                'message': 'Utente non collegato a Keycloak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Salva i ruoli precedenti per confronto
        old_roles = target_user.keycloak_roles.copy() if target_user.keycloak_roles else []
        
        keycloak_service = KeycloakService()
        keycloak_service._sync_user_roles(str(target_user.keycloak_id))
        
        # Ricarica l'utente per ottenere i ruoli aggiornati
        target_user.refresh_from_db()
        new_roles = target_user.keycloak_roles if target_user.keycloak_roles else []
        
        return Response({
            'status': 'success',
            'message': 'Ruoli sincronizzati con successo',
            'user': {
                'id': target_user.id,
                'email': target_user.email,
                'username': target_user.username
            },
            'old_roles': old_roles,
            'new_roles': new_roles,
            'changes': {
                'added': list(set(new_roles) - set(old_roles)),
                'removed': list(set(old_roles) - set(new_roles))
            },
            'last_sync': target_user.last_keycloak_sync,
            'performed_by': request.user.email
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error syncing user roles: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Errore interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)