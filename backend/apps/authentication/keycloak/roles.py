import logging
import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from .base import KeycloakBaseService

logger = logging.getLogger('keycloak')
User = get_user_model()


class KeycloakRoleService(KeycloakBaseService):
    """
    Servizio per la gestione dei ruoli in Keycloak.
    Gestisce l'assegnazione, rimozione e sincronizzazione dei ruoli utente.
    """
    
    def get_realm_roles(self):
        """
        Recupera tutti i ruoli disponibili nel realm.
        """
        try:
            url = f"{self.base_url}/roles"
            response = self._make_authenticated_request('GET', url)
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
        Recupera i ruoli assegnati a un utente specifico.
        """
        try:
            url = f"{self.base_url}/users/{keycloak_id}/role-mappings/realm"
            response = self._make_authenticated_request('GET', url)
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
        Assegna un ruolo a un utente.
        """
        try:
            # Prima ottieni i dettagli del ruolo
            role_url = f"{self.base_url}/roles/{role_name}"
            role_response = self._make_authenticated_request('GET', role_url)
            
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
            
            assign_response = self._make_authenticated_request(
                'POST',
                assign_url,
                json=role_payload,
                headers={'Content-Type': 'application/json'}
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
        Rimuove un ruolo da un utente.
        """
        try:
            # Prima ottieni i dettagli del ruolo
            role_url = f"{self.base_url}/roles/{role_name}"
            role_response = self._make_authenticated_request('GET', role_url)
            
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
            
            remove_response = self._make_authenticated_request(
                'DELETE',
                remove_url,
                json=role_payload,
                headers={'Content-Type': 'application/json'}
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
        Imposta i ruoli di un utente (rimuove tutti i ruoli esistenti e assegna solo quelli specificati).
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
        Sincronizza i ruoli di un utente dal realm Keycloak al database Django.
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