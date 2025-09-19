"""
View di esempio per dimostrare l'uso del sistema di autorizzazione basato sui ruoli Keycloak.

Queste view mostrano diversi modi di utilizzare i decoratori e le classi di permessi
per controllare l'accesso basandosi sui ruoli degli utenti.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from ..permissions import (
    require_keycloak_role,
    require_any_keycloak_role,
    KeycloakRolePermission,
    AdminOnlyPermission,
    EditorPermission,
    ViewerPermission,
    DynamicRolePermission,
    get_user_role_level,
    get_user_highest_role,
    has_keycloak_role,
    is_admin,
    is_editor,
    is_viewer
)


# ============ FUNCTION-BASED VIEWS CON DECORATORI ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_keycloak_role('viewer')
def viewer_content(request):
    """
    Endpoint accessibile a tutti gli utenti autenticati con ruolo viewer o superiore.
    """
    return Response({
        'message': 'Contenuto per viewer',
        'description': 'Questo contenuto è visibile a viewer, editor e admin',
        'user_role_level': get_user_role_level(request.user),
        'user_highest_role': get_user_highest_role(request.user),
        'user_roles': request.user.keycloak_roles
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_keycloak_role('editor')
def editor_content(request):
    """
    Endpoint accessibile solo ad editor e admin.
    """
    if request.method == 'GET':
        return Response({
            'message': 'Contenuto per editor (lettura)',
            'description': 'Questo contenuto è visibile solo a editor e admin',
            'data': [
                {'id': 1, 'name': 'Documento 1', 'status': 'draft'},
                {'id': 2, 'name': 'Documento 2', 'status': 'published'}
            ]
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        return Response({
            'message': 'Contenuto creato con successo',
            'description': 'Solo editor e admin possono creare contenuti',
            'created_item': {
                'id': 3,
                'name': request.data.get('name', 'Nuovo documento'),
                'status': 'draft',
                'created_by': request.user.email
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_keycloak_role('admin')
def admin_content(request):
    """
    Endpoint accessibile solo agli admin.
    """
    if request.method == 'GET':
        return Response({
            'message': 'Pannello di amministrazione',
            'description': 'Questo contenuto è visibile solo agli admin',
            'system_info': {
                'total_users': 150,
                'active_sessions': 23,
                'system_status': 'healthy'
            },
            'admin_actions': [
                'manage_users',
                'view_logs',
                'system_configuration',
                'delete_content'
            ]
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        return Response({
            'message': 'Operazione di eliminazione eseguita',
            'description': 'Solo gli admin possono eliminare risorse',
            'deleted_items': ['item_1', 'item_2']
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_any_keycloak_role(['admin', 'editor'])
def admin_or_editor_content(request):
    """
    Endpoint accessibile ad admin o editor (ma non a viewer).
    """
    return Response({
        'message': 'Contenuto per admin o editor',
        'description': 'Questo contenuto richiede ruolo admin o editor',
        'user_role': 'admin' if is_admin(request.user) else 'editor',
        'available_actions': [
            'create_content',
            'edit_content',
            'publish_content'
        ]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Endpoint per visualizzare il profilo dell'utente con i suoi ruoli.
    """
    return Response({
        'user_info': {
            'id': request.user.id,
            'email': request.user.email,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'keycloak_id': str(request.user.keycloak_id) if request.user.keycloak_id else None
        },
        'authorization_info': {
            'keycloak_roles': request.user.keycloak_roles,
            'role_level': get_user_role_level(request.user),
            'highest_role': get_user_highest_role(request.user),
            'is_admin': is_admin(request.user),
            'is_editor': is_editor(request.user),
            'is_viewer': is_viewer(request.user)
        }
    }, status=status.HTTP_200_OK)


# ============ CLASS-BASED VIEWS CON PERMISSION CLASSES ============

class ViewerOnlyAPIView(APIView):
    """
    Vista che richiede almeno il ruolo viewer.
    """
    authentication_classes = []  # Usa l'autenticazione globale
    permission_classes = [IsAuthenticated, ViewerPermission]
    
    def get(self, request):
        return Response({
            'message': 'Vista per viewer (class-based)',
            'description': 'Implementata usando ViewerPermission',
            'endpoint_type': 'class-based-view'
        })


class EditorOnlyAPIView(APIView):
    """
    Vista che richiede almeno il ruolo editor.
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, EditorPermission]
    
    def get(self, request):
        return Response({
            'message': 'Vista per editor (class-based)',
            'description': 'Implementata usando EditorPermission'
        })
    
    def post(self, request):
        return Response({
            'message': 'Contenuto creato da editor',
            'data': request.data
        }, status=status.HTTP_201_CREATED)


class AdminOnlyAPIView(APIView):
    """
    Vista che richiede il ruolo admin.
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, AdminOnlyPermission]
    
    def get(self, request):
        return Response({
            'message': 'Vista per admin (class-based)',
            'description': 'Implementata usando AdminOnlyPermission'
        })
    
    def delete(self, request):
        return Response({
            'message': 'Risorsa eliminata dall\'admin',
            'description': 'Solo gli admin possono eliminare'
        })


class DynamicRoleAPIView(APIView):
    """
    Vista che usa permessi dinamici basati sul metodo HTTP.
    - GET: viewer+
    - POST/PUT/PATCH: editor+
    - DELETE: admin
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, DynamicRolePermission]
    
    def get(self, request):
        return Response({
            'message': 'Lettura (viewer+)',
            'description': 'GET richiede almeno viewer'
        })
    
    def post(self, request):
        return Response({
            'message': 'Creazione (editor+)',
            'description': 'POST richiede almeno editor'
        }, status=status.HTTP_201_CREATED)
    
    def put(self, request):
        return Response({
            'message': 'Modifica (editor+)',
            'description': 'PUT richiede almeno editor'
        })
    
    def delete(self, request):
        return Response({
            'message': 'Eliminazione (admin)',
            'description': 'DELETE richiede admin'
        })


class CustomRoleAPIView(APIView):
    """
    Vista che usa un permesso personalizzato con ruolo specifico.
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, KeycloakRolePermission('editor')]
    
    def get(self, request):
        return Response({
            'message': 'Vista con permesso personalizzato',
            'description': 'Usa KeycloakRolePermission con ruolo editor',
            'implementation': 'KeycloakRolePermission("editor")'
        })


# ============ ENDPOINT DI UTILITÀ ============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_permissions(request):
    """
    Endpoint per verificare i permessi dell'utente corrente.
    """
    return Response({
        'user': request.user.email,
        'roles': request.user.keycloak_roles,
        'role_checks': {
            'is_admin': is_admin(request.user),
            'is_editor': is_editor(request.user),
            'is_viewer': is_viewer(request.user)
        },
        'role_level': get_user_role_level(request.user),
        'highest_role': get_user_highest_role(request.user),
        'endpoints_accessible': {
            'viewer_content': is_viewer(request.user),
            'editor_content': is_editor(request.user),
            'admin_content': is_admin(request.user)
        }
    })


@api_view(['GET'])
def public_info(request):
    """
    Endpoint pubblico che fornisce informazioni sui ruoli richiesti.
    """
    return Response({
        'message': 'Informazioni sui ruoli Keycloak',
        'roles': {
            'viewer': {
                'level': 1,
                'description': 'Accesso base'
            },
            'editor': {
                'level': 2,
                'description': 'Accesso intermedio'
            },
            'admin': {
                'level': 3,
                'description': 'Accesso completo'
            }
        },
        'endpoints': {
            '/api/v1/auth/roles/viewer/': 'Richiede ruolo viewer o superiore',
            '/api/v1/auth/roles/editor/': 'Richiede ruolo editor o superiore',
            '/api/v1/auth/roles/admin/': 'Richiede ruolo admin',
            '/api/v1/auth/roles/admin-or-editor/': 'Richiede ruolo admin o editor',
            '/api/v1/auth/roles/profile/': 'Richiede autenticazione',
            '/api/v1/auth/roles/check-permissions/': 'Richiede autenticazione'
        }
    })