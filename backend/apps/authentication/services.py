import logging
from .keycloak.auth import KeycloakAuthService
from .keycloak.users import KeycloakUserService
from .keycloak.roles import KeycloakRoleService

logger = logging.getLogger('keycloak')

class KeycloakService:
    def __init__(self):
        self.auth_service = KeycloakAuthService()
        self.user_service = KeycloakUserService()
        self.role_service = KeycloakRoleService()
        self.config = self.auth_service.config
        self.base_url = self.auth_service.base_url
    
    # Metodi delegati al servizio di autenticazione
    def get_admin_token(self):
        """Ottiene un token di amministrazione per le API di Keycloak"""
        return self.auth_service.get_admin_token()
    
    def get_public_key(self):
        """Ottiene la chiave pubblica del realm per la validazione dei JWT"""
        return self.auth_service.get_public_key()
    
    def authenticate_user(self, username, password):
        """Autentica un utente usando username e password tramite Keycloak"""
        return self.auth_service.authenticate_user(username, password)
    
    def validate_token(self, token):
        """Valida un token JWT contro la chiave pubblica di Keycloak"""
        return self.auth_service.validate_token(token)
    
    # Metodi delegati al servizio utenti
    def get_user_by_id(self, keycloak_id):
        """Recupera un utente da Keycloak usando il suo ID"""
        return self.user_service.get_user_by_id(keycloak_id)
    
    def sync_user_from_keycloak(self, keycloak_id):
        """Sincronizza un utente da Keycloak al database Django"""
        return self.user_service.sync_user_from_keycloak(keycloak_id)
    
    def create_user(self, user_data):
        """Crea un nuovo utente sia in Keycloak che in Django"""
        return self.user_service.create_user(user_data)
    
    # Metodi delegati al servizio ruoli
    def get_realm_roles(self):
        """Recupera tutti i ruoli disponibili nel realm"""
        return self.role_service.get_realm_roles()
    
    def get_user_roles(self, keycloak_id):
        """Recupera i ruoli assegnati a un utente specifico"""
        return self.role_service.get_user_roles(keycloak_id)
    
    def assign_role_to_user(self, keycloak_id, role_name):
        """Assegna un ruolo a un utente"""
        return self.role_service.assign_role_to_user(keycloak_id, role_name)
    
    def remove_role_from_user(self, keycloak_id, role_name):
        """Rimuove un ruolo da un utente"""
        return self.role_service.remove_role_from_user(keycloak_id, role_name)
    
    def set_user_roles(self, keycloak_id, role_names):
        """Imposta i ruoli di un utente"""
        return self.role_service.set_user_roles(keycloak_id, role_names)
