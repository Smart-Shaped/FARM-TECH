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

    def get_realm_roles(self):
        """
        Ottiene tutti i ruoli disponibili nel realm
        """
        try:
            token = self.get_admin_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            url = f"{self.base_url}/roles"
            response = requests.get(
                url,
                headers=headers,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            response.raise_for_status()
            
            roles = response.json()
            logger.info(f"Retrieved {len(roles)} roles from Keycloak")
            return {
                'success': True,
                'roles': roles
            }
            
        except Exception as e:
            logger.error(f"Failed to get realm roles: {str(e)}")
            return {
                'success': False,
                'error': 'fetch_roles_failed',
                'message': f'Errore nel recupero dei ruoli: {str(e)}'
            }
    
    def get_user_roles(self, keycloak_id):
        """
        Ottiene i ruoli assegnati a un utente specifico
        """
        try:
            token = self.get_admin_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            url = f"{self.base_url}/users/{keycloak_id}/role-mappings/realm"
            response = requests.get(
                url,
                headers=headers,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            response.raise_for_status()
            
            roles = response.json()
            role_names = [role['name'] for role in roles]
            
            logger.info(f"User {keycloak_id} has roles: {role_names}")
            return {
                'success': True,
                'roles': roles,
                'role_names': role_names
            }
            
        except Exception as e:
            logger.error(f"Failed to get user roles for {keycloak_id}: {str(e)}")
            return {
                'success': False,
                'error': 'fetch_user_roles_failed',
                'message': f'Errore nel recupero dei ruoli utente: {str(e)}'
            }
    
    def assign_role_to_user(self, keycloak_id, role_name):
        """
        Assegna un ruolo a un utente
        """
        try:
            # Prima ottieni il ruolo dal realm
            token = self.get_admin_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            # Ottieni i dettagli del ruolo
            role_url = f"{self.base_url}/roles/{role_name}"
            role_response = requests.get(
                role_url,
                headers=headers,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            
            if role_response.status_code == 404:
                return {
                    'success': False,
                    'error': 'role_not_found',
                    'message': f'Ruolo "{role_name}" non trovato nel realm'
                }
            
            role_response.raise_for_status()
            role_data = role_response.json()
            
            # Assegna il ruolo all'utente
            assign_url = f"{self.base_url}/users/{keycloak_id}/role-mappings/realm"
            role_payload = [role_data]
            
            assign_response = requests.post(
                assign_url,
                json=role_payload,
                headers={**headers, 'Content-Type': 'application/json'},
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            
            if assign_response.status_code == 404:
                return {
                    'success': False,
                    'error': 'user_not_found',
                    'message': f'Utente con ID {keycloak_id} non trovato'
                }
            
            assign_response.raise_for_status()
            
            logger.info(f"Successfully assigned role {role_name} to user {keycloak_id}")
            
            # Sincronizza i ruoli nell'utente Django
            self._sync_user_roles(keycloak_id)
            
            return {
                'success': True,
                'message': f'Ruolo "{role_name}" assegnato con successo',
                'role': role_data
            }
            
        except Exception as e:
            logger.error(f"Failed to assign role {role_name} to user {keycloak_id}: {str(e)}")
            return {
                'success': False,
                'error': 'assign_role_failed',
                'message': f'Errore nell\'assegnazione del ruolo: {str(e)}'
            }
    
    def remove_role_from_user(self, keycloak_id, role_name):
        """
        Rimuove un ruolo da un utente
        """
        try:
            # Prima ottieni il ruolo dal realm
            token = self.get_admin_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            # Ottieni i dettagli del ruolo
            role_url = f"{self.base_url}/roles/{role_name}"
            role_response = requests.get(
                role_url,
                headers=headers,
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            
            if role_response.status_code == 404:
                return {
                    'success': False,
                    'error': 'role_not_found',
                    'message': f'Ruolo "{role_name}" non trovato nel realm'
                }
            
            role_response.raise_for_status()
            role_data = role_response.json()
            
            # Rimuovi il ruolo dall'utente
            remove_url = f"{self.base_url}/users/{keycloak_id}/role-mappings/realm"
            role_payload = [role_data]
            
            remove_response = requests.delete(
                remove_url,
                json=role_payload,
                headers={**headers, 'Content-Type': 'application/json'},
                verify=self.config['VERIFY_SSL'],
                timeout=10
            )
            
            if remove_response.status_code == 404:
                return {
                    'success': False,
                    'error': 'user_not_found',
                    'message': f'Utente con ID {keycloak_id} non trovato'
                }
            
            remove_response.raise_for_status()
            
            logger.info(f"Successfully removed role {role_name} from user {keycloak_id}")
            
            # Sincronizza i ruoli nell'utente Django
            self._sync_user_roles(keycloak_id)
            
            return {
                'success': True,
                'message': f'Ruolo "{role_name}" rimosso con successo',
                'role': role_data
            }
            
        except Exception as e:
            logger.error(f"Failed to remove role {role_name} from user {keycloak_id}: {str(e)}")
            return {
                'success': False,
                'error': 'remove_role_failed',
                'message': f'Errore nella rimozione del ruolo: {str(e)}'
            }
    
    def set_user_roles(self, keycloak_id, role_names):
        """
        Imposta i ruoli di un utente (rimuove tutti i ruoli esistenti e assegna solo quelli specificati)
        """
        try:
            # Prima ottieni i ruoli attuali dell'utente
            current_roles_result = self.get_user_roles(keycloak_id)
            if not current_roles_result['success']:
                return current_roles_result
            
            current_role_names = current_roles_result['role_names']
            
            # Ruoli da rimuovere (quelli attuali che non sono nella nuova lista)
            roles_to_remove = set(current_role_names) - set(role_names)
            # Ruoli da aggiungere (quelli nella nuova lista che non sono attuali)
            roles_to_add = set(role_names) - set(current_role_names)
            
            results = []
            
            # Rimuovi i ruoli non più necessari
            for role_name in roles_to_remove:
                result = self.remove_role_from_user(keycloak_id, role_name)
                results.append(f"Remove {role_name}: {'success' if result['success'] else 'failed'}")
            
            # Aggiungi i nuovi ruoli
            for role_name in roles_to_add:
                result = self.assign_role_to_user(keycloak_id, role_name)
                results.append(f"Add {role_name}: {'success' if result['success'] else 'failed'}")
            
            logger.info(f"Set roles for user {keycloak_id}: {results}")
            
            return {
                'success': True,
                'message': f'Ruoli impostati con successo: {role_names}',
                'operations': results,
                'final_roles': role_names
            }
            
        except Exception as e:
            logger.error(f"Failed to set roles for user {keycloak_id}: {str(e)}")
            return {
                'success': False,
                'error': 'set_roles_failed',
                'message': f'Errore nell\'impostazione dei ruoli: {str(e)}'
            }
    
    def _sync_user_roles(self, keycloak_id):
        """
        Sincronizza i ruoli di un utente dal realm Keycloak al database Django
        """
        try:
            # Ottieni i ruoli aggiornati da Keycloak
            roles_result = self.get_user_roles(keycloak_id)
            if not roles_result['success']:
                return
            
            # Trova l'utente Django
            try:
                user = User.objects.get(keycloak_id=keycloak_id)
                user.keycloak_roles = roles_result['role_names']
                user.last_keycloak_sync = timezone.now()
                user.save()
                
                logger.info(f"Synced roles for user {user.email}: {user.keycloak_roles}")
                
            except User.DoesNotExist:
                logger.warning(f"Django user with keycloak_id {keycloak_id} not found for role sync")
        
        except Exception as e:
            logger.error(f"Failed to sync user roles: {str(e)}")
