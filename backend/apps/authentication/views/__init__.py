from .health_views import keycloak_health_check, keycloak_config, protected_endpoint
from .auth_views import login, validate_token, validate_jwt_token
from .user_views import register

__all__ = [
    # Health & Config views
    'keycloak_health_check',
    'keycloak_config', 
    'protected_endpoint',
    
    # Authentication views
    'login',
    'validate_token',
    'validate_jwt_token',
    
    # User management views
    'register',
]