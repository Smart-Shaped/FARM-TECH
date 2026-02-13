"""
Keycloak authentication for FarmTech application.
"""

import logging
import jwt
from jwt import PyJWKClient
from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings


logger = logging.getLogger(__name__)
User = get_user_model()


class KeycloakAuthentication(authentication.BaseAuthentication):
    """
    Keycloak authentication for FarmTech application.
    """

    def authenticate(self, request):
        """
        Authenticate user based on Keycloak token.
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            keycloak_config = getattr(settings, "SOCIALACCOUNT_PROVIDERS_DEFS", {}).get(
                "keycloak", {}
            )

            if not keycloak_config:
                keycloak_config = getattr(
                    settings, "_KEYCLOAK_SOCIALACCOUNT_PROVIDER", {}
                )

            issuer = keycloak_config.get("ID_TOKEN_ISSUER")

            if not issuer:
                raise exceptions.AuthenticationFailed("Keycloak configuration missing")

            jwks_uri = f"{issuer}/protocol/openid-connect/certs"

            jwks_client = PyJWKClient(jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            decode_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
            }

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=issuer,
                audience=getattr(settings, "KEYCLOAK_CLIENT_ID", {}),
                options=decode_options,
            )

            username = payload.get("preferred_username")
            email = payload.get("email", "")
            first_name = payload.get("given_name", "")
            last_name = payload.get("family_name", "")

            if not username:
                raise exceptions.AuthenticationFailed("Username not found in token")

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )

            if not created:
                if email:
                    user.email = email
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                user.save()
            else:
                try:
                    anonymous_group, _ = Group.objects.get_or_create(name="anonymous")
                    registered_group, _ = Group.objects.get_or_create(
                        name="registered-members"
                    )
                    user.groups.add(anonymous_group, registered_group)
                    logger.info(
                        "Groups 'anonymous' and 'registered-members' assigned to user %s",
                        username,
                    )
                except Exception as e:
                    logger.exception(
                        "Error assigning groups to user %s: %s",
                        username,
                        str(e),
                        exc_info=True,
                    )

            return (user, token)

        except jwt.ExpiredSignatureError as e:
            logger.exception("Expired token: %s", str(e), exc_info=True)
            raise exceptions.AuthenticationFailed("Expired token") from e
        except jwt.InvalidTokenError as e:
            logger.exception("Invalid token: %s", str(e), exc_info=True)
            raise exceptions.AuthenticationFailed("Invalid token") from e
        except Exception as e:
            logger.exception("Keycloak authentication error: %s", str(e), exc_info=True)
            raise exceptions.AuthenticationFailed("Keycloak authentication error.")
