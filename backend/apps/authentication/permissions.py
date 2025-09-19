"""
Sistema di autorizzazione basato sui ruoli di Keycloak.

Questo modulo fornisce decoratori e classi di permessi per controllare l'accesso
alle API basandosi esclusivamente sui ruoli assegnati agli utenti in Keycloak.

Ruoli supportati:
- admin: Accesso completo a tutte le risorse
- editor: Accesso di livello intermedio
- viewer: Accesso base
"""

from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

# Definizione dei ruoli e delle loro gerarchie (solo livelli, niente permissioni)
ROLES = {
    'admin': {'level': 3},
    'editor': {'level': 2},
    'viewer': {'level': 1}
}

def has_keycloak_role(user, required_role):
    """
    Verifica se l'utente ha il ruolo richiesto o uno superiore.
    
    Args:
        user: L'oggetto User Django
        required_role: Il ruolo minimo richiesto ('admin', 'editor', 'viewer')
    
    Returns:
        bool: True se l'utente ha il ruolo richiesto o superiore
    """
    if not user or not user.is_authenticated:
        return False
    
    user_roles = getattr(user, 'keycloak_roles', [])
    
    if not user_roles:
        logger.warning(f"User {user.email} has no Keycloak roles")
        return False
    
    # Verifica se l'utente ha il ruolo esatto
    if required_role in user_roles:
        return True
    
    # Verifica se l'utente ha un ruolo di livello superiore
    required_level = ROLES.get(required_role, {}).get('level', 0)
    
    for role in user_roles:
        if role in ROLES:
            user_level = ROLES[role]['level']
            if user_level >= required_level:
                return True
    
    return False


def require_keycloak_role(required_role):
    """
    Decoratore per view function-based che richiede un ruolo specifico.
    
    Args:
        required_role: Il ruolo minimo richiesto ('admin', 'editor', 'viewer')
    
    Usage:
        @require_keycloak_role('admin')
        def my_admin_view(request):
            return JsonResponse({'message': 'Admin only content'})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_keycloak_role(request.user, required_role):
                return JsonResponse({
                    'error': 'Insufficient role',
                    'message': f'This endpoint requires {required_role} role or higher',
                    'required_role': required_role,
                    'user_roles': getattr(request.user, 'keycloak_roles', []) if request.user.is_authenticated else []
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class KeycloakRolePermission(BasePermission):
    """
    Classe di permessi per Django REST Framework che verifica i ruoli Keycloak.
    
    Può essere usata in due modi:
    1. Come classe base - richiede di sovrascrivere get_required_role()
    2. Istanziata con un ruolo specifico
    
    Usage:
        # Metodo 1 - Classe personalizzata
        class AdminOnlyPermission(KeycloakRolePermission):
            def get_required_role(self):
                return 'admin'
        
        # Metodo 2 - Istanza diretta
        permission_classes = [KeycloakRolePermission('editor')]
    """
    
    def __init__(self, required_role=None):
        self.required_role = required_role
    
    def has_permission(self, request, view):
        """
        Verifica se l'utente ha il ruolo necessario per accedere alla view.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        required_role = self.get_required_role(request, view)
        
        if not required_role:
            logger.warning(f"No required role specified for {view.__class__.__name__}")
            return False
        
        has_role = has_keycloak_role(request.user, required_role)
        
        if not has_role:
            logger.warning(
                f"User {request.user.email} with roles {request.user.keycloak_roles} "
                f"attempted to access {view.__class__.__name__} requiring {required_role}"
            )
        
        return has_role
    
    def get_required_role(self, request=None, view=None):
        """
        Ottiene il ruolo richiesto per questa view.
        Può essere sovrascritta nelle sottoclassi per logica dinamica.
        """
        if self.required_role:
            return self.required_role
        
        # Se non specificato, prova a leggere dall'attributo della view
        if view and hasattr(view, 'required_role'):
            return view.required_role
        
        return None


class AdminOnlyPermission(KeycloakRolePermission):
    """Permesso che richiede il ruolo 'admin'"""
    def get_required_role(self, request=None, view=None):
        return 'admin'


class EditorPermission(KeycloakRolePermission):
    """Permesso che richiede il ruolo 'editor' o superiore"""
    def get_required_role(self, request=None, view=None):
        return 'editor'


class ViewerPermission(KeycloakRolePermission):
    """Permesso che richiede il ruolo 'viewer' o superiore"""
    def get_required_role(self, request=None, view=None):
        return 'viewer'


class DynamicRolePermission(KeycloakRolePermission):
    """
    Permesso che determina il ruolo richiesto basandosi sul metodo HTTP.
    
    - GET: viewer o superiore
    - POST/PUT/PATCH: editor o superiore  
    - DELETE: admin
    """
    
    def get_required_role(self, request=None, view=None):
        if not request:
            return 'viewer'
        
        method = request.method.upper()
        
        if method in ['DELETE']:
            return 'admin'
        elif method in ['POST', 'PUT', 'PATCH']:
            return 'editor'
        else:  # GET, HEAD, OPTIONS
            return 'viewer'


def require_any_keycloak_role(required_roles):
    """
    Decoratore che richiede almeno uno dei ruoli specificati.
    
    Args:
        required_roles: Lista di ruoli accettati
    
    Usage:
        @require_any_keycloak_role(['admin', 'editor'])
        def my_view(request):
            return JsonResponse({'message': 'Admin or editor content'})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required',
                    'message': 'This endpoint requires authentication'
                }, status=401)
            
            user_roles = getattr(request.user, 'keycloak_roles', [])
            
            # Verifica se l'utente ha almeno uno dei ruoli richiesti
            has_required_role = any(
                has_keycloak_role(request.user, role) for role in required_roles
            )
            
            if not has_required_role:
                return JsonResponse({
                    'error': 'Insufficient role',
                    'message': f'This endpoint requires one of these roles: {", ".join(required_roles)}',
                    'required_roles': required_roles,
                    'user_roles': user_roles
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_user_role_level(user):
    """
    Ottiene il livello di ruolo più alto dell'utente.
    
    Args:
        user: L'oggetto User Django
    
    Returns:
        int: Il livello più alto (3=admin, 2=editor, 1=viewer, 0=nessun ruolo)
    """
    if not user or not user.is_authenticated:
        return 0
    
    user_roles = getattr(user, 'keycloak_roles', [])
    max_level = 0
    
    for role in user_roles:
        if role in ROLES:
            level = ROLES[role]['level']
            max_level = max(max_level, level)
    
    return max_level


def get_user_highest_role(user):
    """
    Ottiene il ruolo più alto dell'utente.
    
    Args:
        user: L'oggetto User Django
    
    Returns:
        str: Il ruolo più alto ('admin', 'editor', 'viewer', None)
    """
    if not user or not user.is_authenticated:
        return None
    
    user_roles = getattr(user, 'keycloak_roles', [])
    
    # Controlla in ordine di priorità
    if 'admin' in user_roles:
        return 'admin'
    elif 'editor' in user_roles:
        return 'editor'
    elif 'viewer' in user_roles:
        return 'viewer'
    
    return None


def is_admin(user):
    """Verifica se l'utente ha il ruolo admin"""
    return has_keycloak_role(user, 'admin')


def is_editor(user):
    """Verifica se l'utente ha il ruolo editor o superiore"""
    return has_keycloak_role(user, 'editor')


def is_viewer(user):
    """Verifica se l'utente ha il ruolo viewer o superiore"""
    return has_keycloak_role(user, 'viewer')