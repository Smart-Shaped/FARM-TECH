import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .authentication import KeycloakJWTAuthentication

logger = logging.getLogger('keycloak')


class KeycloakJWTMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth = KeycloakJWTAuthentication()
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Processa la richiesta per autenticare l'utente
        """
        # Skip per endpoint pubblici
        if self._is_public_endpoint(request.path):
            return None
        
        try:
            # Tenta l'autenticazione
            auth_result = self.auth.authenticate(request)
            
            if auth_result:
                user, token = auth_result
                request.user = user
                request.auth = token
                logger.debug(f"User authenticated: {user.email}")
                
        except Exception as e:
            logger.warning(f"Authentication failed: {str(e)}")
            # Non bloccare la richiesta, lascia che DRF gestisca
            pass
        
        return None
    
    def _is_public_endpoint(self, path):
        """
        Determina se l'endpoint è pubblico
        """
        public_paths = [
            '/api/v1/health/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)