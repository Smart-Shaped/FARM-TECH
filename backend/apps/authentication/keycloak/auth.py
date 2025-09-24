import jwt
import logging
import requests
from .base import KeycloakBaseService

logger = logging.getLogger('keycloak')

class KeycloakAuthService(KeycloakBaseService):
    """
    Servizio per la gestione dell'autenticazione utenti con Keycloak.
    Gestisce login, logout e validazione dei token JWT.
    """
    
    def authenticate_user(self, username, password):
        """
        Autentica un utente usando username e password tramite Keycloak.
        Restituisce i token di accesso se l'autenticazione ha successo.
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
        Valida un token JWT contro la chiave pubblica di Keycloak.
        Restituisce i dati dell'utente se il token è valido.
        """
        try:
            public_key_str = self.get_public_key()
            
            public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"
            
            decoded_token = jwt.decode(
                token,
                public_key_pem,
                algorithms=self.config['ALGORITHMS'],
                audience=self.config['AUDIENCE'],
                issuer=f"{self.config['SERVER_URL']}/realms/{self.config['REALM']}",
                leeway=30  # Tollera 30 secondi di differenza di tempo tra i server
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
        except jwt.ImmatureSignatureError:
            logger.warning("Token not yet valid (issued in the future)")
            return {
                'valid': False,
                'error': 'token_not_yet_valid',
                'message': 'Token non ancora valido'
            }
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return {
                'valid': False,
                'error': 'invalid_token',
                'message': f'Token non valido: {str(e)}'
            }
        except Exception as e:
            # Per debug: logga i dettagli del token se possibile
            try:
                import time
                # Decodifica senza verifica per vedere i timestamp
                unverified_token = jwt.decode(token, options={"verify_signature": False})
                current_time = int(time.time())
                iat = unverified_token.get('iat', 'missing')
                exp = unverified_token.get('exp', 'missing')
                logger.error(f"Token validation error: {str(e)} - Current time: {current_time}, IAT: {iat}, EXP: {exp}")
            except:
                logger.error(f"Token validation error: {str(e)}")
            
            return {
                'valid': False,
                'error': 'validation_error',
                'message': f'Errore di validazione: {str(e)}'
            }