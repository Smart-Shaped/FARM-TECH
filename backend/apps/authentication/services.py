import requests
import logging
import jwt
import base64
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger('keycloak')
User = get_user_model()


class KeycloakService:
    """
    Servizio per interagire con Keycloak
    """
    
    def __init__(self):
        self.config = settings.KEYCLOAK_CONFIG
        self.base_url = f"{self.config['SERVER_URL']}/admin/realms/{self.config['REALM']}"
    
    def get_admin_token(self):
        """
        Ottiene un token di amministrazione per Keycloak
        """
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
    
    def get_user_by_id(self, keycloak_id):
        """
        Ottiene i dati di un utente da Keycloak
        """
        try:
            token = self.get_admin_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            url = f"{self.base_url}/users/{keycloak_id}"
            response = requests.get(
                url,
                headers=headers,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get user {keycloak_id}: {str(e)}")
            return None
    
    def sync_user_from_keycloak(self, keycloak_id):
        """
        Sincronizza un utente da Keycloak
        """
        keycloak_data = self.get_user_by_id(keycloak_id)
        
        if not keycloak_data:
            return None
        
        try:
            user = User.objects.get(keycloak_id=keycloak_id)
            user.update_from_keycloak(keycloak_data)
            logger.info(f"Updated user {user.email} from Keycloak")
            
        except User.DoesNotExist:
            # Crea nuovo utente
            user = User.objects.create(
                keycloak_id=keycloak_id,
                username=keycloak_data.get('username'),
                email=keycloak_data.get('email'),
                first_name=keycloak_data.get('firstName', ''),
                last_name=keycloak_data.get('lastName', ''),
                is_active=keycloak_data.get('enabled', True),
                last_keycloak_sync=timezone.now()
            )
            logger.info(f"Created user {user.email} from Keycloak")
        
        return user
    
    def get_public_key(self):
        """
        Ottiene la chiave pubblica del realm da Keycloak
        """
        cache_key = f'keycloak_public_key_{self.config["REALM"]}'
        public_key = cache.get(cache_key)
        
        if not public_key:
            try:
                # Prova prima l'endpoint del realm base per ottenere la chiave pubblica
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
    
    def authenticate_user(self, username, password):
        """
        Autentica un utente con Keycloak usando username e password
        """
        try:
            token_url = f"{self.config['SERVER_URL']}/realms/{self.config['REALM']}/protocol/openid-connect/token"
            
            data = {
                'grant_type': 'password',
                'client_id': self.config['CLIENT_ID'],
                'client_secret': self.config['CLIENT_SECRET'],
                'username': username,
                'password': password,
                'scope': 'openid profile email'
            }
            
            response = requests.post(
                token_url,
                data=data,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                logger.info(f"Successfully authenticated user: {username}")
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in'),
                    'token_type': token_data.get('token_type', 'Bearer')
                }
            elif response.status_code == 401:
                logger.warning(f"Authentication failed for user: {username}")
                return {
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Username o password non validi'
                }
            else:
                logger.error(f"Keycloak authentication error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': 'authentication_error',
                    'message': f'Errore di autenticazione: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Authentication exception: {str(e)}")
            return {
                'success': False,
                'error': 'connection_error',
                'message': f'Errore di connessione: {str(e)}'
            }
    
    def validate_token(self, token):
        """
        Valida un token JWT di Keycloak
        """
        try:
            # Ottieni la chiave pubblica
            public_key_str = self.get_public_key()
            
            # Converti la chiave pubblica in formato PEM
            public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"
            
            # Decodifica e valida il token
            decoded_token = jwt.decode(
                token,
                public_key_pem,
                algorithms=self.config['ALGORITHMS'],
                audience=self.config['AUDIENCE'],
                issuer=f"{self.config['SERVER_URL']}/realms/{self.config['REALM']}"
            )
            
            logger.info(f"Token validated successfully for user: {decoded_token.get('preferred_username')}")
            
            return {
                'valid': True,
                'user_data': {
                    'keycloak_id': decoded_token.get('sub'),
                    'username': decoded_token.get('preferred_username'),
                    'email': decoded_token.get('email'),
                    'first_name': decoded_token.get('given_name'),
                    'last_name': decoded_token.get('family_name'),
                    'roles': decoded_token.get('realm_access', {}).get('roles', [])
                },
                'token_data': decoded_token
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return {
                'valid': False,
                'error': 'token_expired',
                'message': 'Token scaduto'
            }
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return {
                'valid': False,
                'error': 'invalid_token',
                'message': f'Token non valido: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {
                'valid': False,
                'error': 'validation_error',
                'message': f'Errore di validazione: {str(e)}'
            }
    
    def create_user(self, user_data):
        """
        Crea un nuovo utente in Keycloak
        """
        try:
            token = self.get_admin_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Prepara i dati per Keycloak
            keycloak_user_data = {
                'username': user_data['username'],
                'email': user_data['email'],
                'firstName': user_data.get('first_name', ''),
                'lastName': user_data.get('last_name', ''),
                'enabled': True,
                'emailVerified': True,
                'credentials': [{
                    'type': 'password',
                    'value': user_data['password'],
                    'temporary': False
                }]
            }
            
            # Crea l'utente in Keycloak
            url = f"{self.base_url}/users"
            response = requests.post(
                url,
                json=keycloak_user_data,
                headers=headers,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            
            if response.status_code == 201:
                # Ottieni l'ID dell'utente creato dall'header Location
                location = response.headers.get('Location')
                if location:
                    keycloak_id = location.split('/')[-1]
                    
                    # Crea l'utente anche in Django
                    django_user = User.objects.create(
                        keycloak_id=keycloak_id,
                        username=user_data['username'],
                        email=user_data['email'],
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                        is_active=True,
                        last_keycloak_sync=timezone.now()
                    )
                    
                    logger.info(f"Successfully created user {user_data['email']} in Keycloak and Django")
                    
                    return {
                        'success': True,
                        'keycloak_id': keycloak_id,
                        'django_user': django_user,
                        'message': 'Utente creato con successo'
                    }
                else:
                    raise Exception("Location header not found in response")
                    
            elif response.status_code == 409:
                return {
                    'success': False,
                    'error': 'user_exists',
                    'message': 'Utente già esistente'
                }
            else:
                logger.error(f"Failed to create user in Keycloak: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': 'creation_failed',
                    'message': f'Errore nella creazione: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"User creation exception: {str(e)}")
            return {
                'success': False,
                'error': 'connection_error',
                'message': f'Errore di connessione: {str(e)}'
            }