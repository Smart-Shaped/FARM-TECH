import logging
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from .base import KeycloakBaseService

logger = logging.getLogger('keycloak')
User = get_user_model()


class KeycloakUserService(KeycloakBaseService):
    """
    Servizio per la gestione degli utenti in Keycloak.
    Gestisce creazione, modifica, sincronizzazione e recupero degli utenti.
    """
    
    def get_user_by_id(self, keycloak_id):
        """
        Recupera un utente da Keycloak usando il suo ID.
        """
        try:
            url = f"{self.base_url}/users/{keycloak_id}"
            response = self._make_authenticated_request('GET', url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get user {keycloak_id}: {str(e)}")
            return None
    
    def sync_user_from_keycloak(self, keycloak_id):
        """
        Sincronizza un utente da Keycloak al database Django.
        Se l'utente non esiste in Django, lo crea.
        """
        keycloak_data = self.get_user_by_id(keycloak_id)
        
        if not keycloak_data:
            return None
        
        try:
            user = User.objects.get(keycloak_id=keycloak_id)
            user.update_from_keycloak(keycloak_data)
            logger.info(f"Updated user {user.email} from Keycloak")
            
        except User.DoesNotExist:
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
    
    def create_user(self, user_data):
        """
        Crea un nuovo utente sia in Keycloak che in Django.
        """
        try:
            headers = {'Content-Type': 'application/json'}
            
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
            
            url = f"{self.base_url}/users"
            response = self._make_authenticated_request(
                'POST', 
                url, 
                json=keycloak_user_data,
                headers=headers
            )
            
            if response.status_code == 201:
                location = response.headers.get('Location')
                if location:
                    keycloak_id = location.split('/')[-1]
                    
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