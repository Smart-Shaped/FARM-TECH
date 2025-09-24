"""
Modulo Keycloak modularizzato per la gestione dell'autenticazione e autorizzazione.

Questo modulo è suddiviso in:
- base: Configurazione base e operazioni comuni
- auth: Autenticazione utenti e validazione token
- users: Gestione degli utenti (CRUD)
- roles: Gestione dei ruoli e autorizzazioni
"""

from .auth import KeycloakAuthService
from .users import KeycloakUserService  
from .roles import KeycloakRoleService
from .base import KeycloakBaseService

__all__ = [
    'KeycloakAuthService',
    'KeycloakUserService', 
    'KeycloakRoleService',
    'KeycloakBaseService'
]
