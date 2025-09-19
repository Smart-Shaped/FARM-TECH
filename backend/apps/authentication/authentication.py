import jwt
import requests
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger('keycloak')
User = get_user_model()

class KeycloakJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decodifica e valida il token
            payload = self._decode_token(token)
            
            # Ottieni o crea l'utente
            user = self._get_or_create_user(payload)
            
            return (user, token)
            
        except Exception as e:
            logger.error(f"JWT Authentication failed: {str(e)}")
            raise AuthenticationFailed('Invalid token')
    
    def _decode_token(self, token):
        try:
            # Ottieni la chiave pubblica di Keycloak (con cache)
            public_key = self._get_keycloak_public_key()
            
            logger.debug(f"Attempting to decode token with public key")
            logger.debug(f"Token starts with: {token[:50]}...")
            
            # Decodifica il token con le stesse opzioni che funzionano nel KeycloakService
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],  # Usa RS256 esplicitamente
                # Rimuovi audience per ora per testare
                options={
                    "verify_exp": True,
                    "verify_aud": False  # Disabilita verifica audience temporaneamente
                }
            )
            
            logger.debug(f"Token decoded successfully. Subject: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            logger.error(f"Token decode error: {str(e)}")
            raise AuthenticationFailed(f'Token decode error: {str(e)}')
    
    def _get_keycloak_public_key(self):
        cache_key = 'keycloak_public_key'
        public_key = cache.get(cache_key)
        
        if not public_key:
            try:
                logger.debug("Fetching Keycloak public key from realm endpoint")
                
                # URL per ottenere la configurazione del realm (stesso metodo del KeycloakService)
                realm_url = (
                    f"{settings.KEYCLOAK_CONFIG['SERVER_URL']}/realms/"
                    f"{settings.KEYCLOAK_CONFIG['REALM']}"
                )
                
                logger.debug(f"Requesting realm data from: {realm_url}")
                
                response = requests.get(
                    realm_url,
                    verify=settings.KEYCLOAK_CONFIG.get('VERIFY_SSL', True),
                    timeout=10
                )
                response.raise_for_status()
                
                realm_data = response.json()
                
                # Ottieni la chiave pubblica dal realm
                public_key_str = realm_data.get('public_key')
                if not public_key_str:
                    raise Exception("Public key not found in realm data")
                
                logger.debug(f"Public key retrieved: {public_key_str[:50]}...")
                
                # Converti in formato PEM
                public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"
                
                # Cache per 1 ora
                cache.set(cache_key, public_key_pem, 3600)
                public_key = public_key_pem
                
                logger.debug("Public key cached successfully")
                
            except Exception as e:
                logger.error(f"Failed to get Keycloak public key: {str(e)}")
                raise AuthenticationFailed(f'Unable to verify token: {str(e)}')
        else:
            logger.debug("Using cached public key")
        
        return public_key
    
    def _get_or_create_user(self, payload):
        """
        Ottiene o crea l'utente basandosi sui dati del token
        """
        keycloak_id = payload.get('sub')
        email = payload.get('email')
        username = payload.get('preferred_username')
        first_name = payload.get('given_name', '')
        last_name = payload.get('family_name', '')
        
        # Estrai i ruoli dal token
        roles = []
        if 'realm_access' in payload:
            roles = payload['realm_access'].get('roles', [])
        elif 'roles' in payload:
            roles = payload['roles']
        
        if not keycloak_id:
            raise AuthenticationFailed('Invalid token: missing subject')
        
        # Se non c'è email, usa username come email o crea un email fittizio
        if not email:
            if username:
                email = f"{username}@keycloak.local"
            else:
                email = f"{keycloak_id}@keycloak.local"
        
        # Se non c'è username, usa l'email come username
        if not username:
            username = email.split('@')[0]
        
        try:
            # Cerca l'utente per keycloak_id
            user = User.objects.get(keycloak_id=keycloak_id)
            
            # Aggiorna i dati se necessario (ma non sovrascrivere email se è già impostata)
            updated = False
            if user.email != email and not user.email:
                user.email = email
                updated = True
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if user.keycloak_roles != roles:
                user.keycloak_roles = roles
                updated = True
                
            if updated:
                user.save()
                
        except User.DoesNotExist:
            # Crea nuovo utente
            user = User.objects.create(
                keycloak_id=keycloak_id,
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                keycloak_roles=roles,
                is_active=True
            )
            logger.info(f"Created new user from Keycloak: {username} ({email}) with roles: {roles}")
        
        logger.debug(f"User {user.email} authenticated with roles: {user.keycloak_roles}")
        return user