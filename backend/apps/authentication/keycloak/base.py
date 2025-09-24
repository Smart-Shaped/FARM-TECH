import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('keycloak')


class KeycloakBaseService:
    """
    Classe base per tutti i servizi Keycloak che gestisce la configurazione 
    e le operazioni comuni come l'autenticazione admin.
    """
    
    def __init__(self):
        self.config = settings.KEYCLOAK_CONFIG
        self.base_url = f"{self.config['SERVER_URL']}/admin/realms/{self.config['REALM']}"
    
    def get_admin_token(self):
        """Ottiene un token di amministrazione per le API di Keycloak"""
        cache_key = 'keycloak_admin_token'
        token = cache.get(cache_key)
        
        if not token:
            try:
                token_url = f"{self.config['SERVER_URL']}/realms/{self.config['REALM']}/protocol/openid-connect/token"
                
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.config['CLIENT_ID'],
                    'client_secret': self.config['CLIENT_SECRET'],
                }
                
                response = requests.post(
                    token_url,
                    data=data,
                    verify=self.config['VERIFY_SSL'],
                    timeout=10
                )
                response.raise_for_status()
                
                token_data = response.json()
                token = token_data['access_token']
                
                # Cache per 5 minuti (meno della scadenza del token)
                cache.set(cache_key, token, 300)
                
            except Exception as e:
                logger.error(f"Failed to get admin token: {str(e)}")
                raise
        
        return token
    
    def get_public_key(self):
        """Ottiene la chiave pubblica del realm per la validazione dei JWT"""
        cache_key = f'keycloak_public_key_{self.config["REALM"]}'
        public_key = cache.get(cache_key)
        
        if not public_key:
            try:
                realm_url = f"{self.config['SERVER_URL']}/realms/{self.config['REALM']}"
                
                response = requests.get(
                    realm_url,
                    verify=self.config['VERIFY_SSL'],
                    timeout=10
                )
                response.raise_for_status()
                
                realm_data = response.json()
                public_key = realm_data.get('public_key')
                
                if not public_key:
                    raise ValueError("Public key not found in realm data")
                
                # Cache per 1 ora (le chiavi pubbliche cambiano raramente)
                cache.set(cache_key, public_key, 3600)
                
                logger.info(f"Successfully retrieved public key for realm {self.config['REALM']}")
                
            except Exception as e:
                logger.error(f"Failed to get public key: {str(e)}")
                raise
        
        return public_key
    
    def _make_authenticated_request(self, method, url, **kwargs):
        """
        Helper per fare richieste autenticate alle API di Keycloak
        """
        token = self.get_admin_token()
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        kwargs.setdefault('verify', self.config['VERIFY_SSL'])
        kwargs.setdefault('timeout', 10)
        
        return requests.request(method, url, **kwargs)