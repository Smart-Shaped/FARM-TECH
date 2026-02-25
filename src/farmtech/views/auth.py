"""
Keycloak authentication API view for FarmTech application.
"""

import logging
import re
from urllib.parse import urlencode
import traceback
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, logout, login
from django.contrib.auth.models import Group
from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from django.utils.http import url_has_allowed_host_and_scheme
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from farmtech.throttles import IPBasedThrottle


logger = logging.getLogger(__name__)
User = get_user_model()


def _get_keycloak_config():
    """Retrieve Keycloak configuration from Django settings."""
    keycloak_config = getattr(settings, "SOCIALACCOUNT_PROVIDERS_DEFS", {}).get(
        "keycloak", {}
    )
    if not keycloak_config:
        keycloak_config = getattr(settings, "_KEYCLOAK_SOCIALACCOUNT_PROVIDER", {})
    return keycloak_config


def _get_keycloak_admin_base_url(issuer):
    """
    Derive the Keycloak admin API base URL and realm from the issuer URL.
    Supports both Keycloak >=17 and legacy (<=16) issuer formats:
      - http(s)://host(:port)/realms/{realm}          (Keycloak >=17)
      - http(s)://host(:port)/auth/realms/{realm}     (Keycloak <=16)
    Returns (base_url, realm) where base_url includes /auth when present,
    so the admin API can be built as: {base_url}/admin/realms/{realm}
    """
    match = re.match(r"(https?://[^/]+(?:/auth)?)/realms/(.+?)/?$", issuer)
    if not match:
        logger.error(
            "Could not parse Keycloak issuer URL: '%s'. "
            "Expected format: http(s)://host(:port)[/auth]/realms/{realm}",
            issuer,
        )
        return None, None
    base_url = match.group(1)
    realm = match.group(2)
    return base_url, realm


class KeycloakAuthAPIView(APIView):
    """API view for authenticating users via Keycloak."""

    throttle_classes = [IPBasedThrottle]

    @swagger_auto_schema(
        operation_description="Authenticate user via Keycloak and return Django token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Authentication successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "token": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Django authentication token",
                        ),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        "keycloak_access_token": openapi.Schema(
                            type=openapi.TYPE_STRING
                        ),
                        "keycloak_refresh_token": openapi.Schema(
                            type=openapi.TYPE_STRING
                        ),
                        "expires_in": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            400: openapi.Response(description="Username and password are required"),
            401: openapi.Response(description="Invalid credentials"),
            500: openapi.Response(
                description="Keycloak configuration missing or connection error"
            ),
        },
    )
    def post(self, request):
        """Handle POST request for Keycloak authentication."""
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        keycloak_config = _get_keycloak_config()

        token_url = keycloak_config.get("ACCESS_TOKEN_URL")
        userinfo_url = keycloak_config.get("PROFILE_URL")
        keycloak_client_id = keycloak_config.get("CLIENT_ID")
        keycloak_client_secret = keycloak_config.get("SECRET")
        verify_ssl = keycloak_config.get("VERIFY_SSL", True)

        if not all([token_url, userinfo_url, keycloak_client_id]):
            return Response(
                {
                    "error": "Keycloak configuration missing",
                    "debug": {
                        "token_url": token_url,
                        "userinfo_url": userinfo_url,
                        "client_id": keycloak_client_id,
                        "has_secret": bool(keycloak_client_secret),
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        token_data = {
            "grant_type": "password",
            "client_id": keycloak_client_id,
            "username": username,
            "password": password,
            "scope": "openid profile email",
        }

        if keycloak_client_secret:
            token_data["client_secret"] = keycloak_client_secret

        try:
            token_response = requests.post(
                token_url, data=token_data, verify=verify_ssl, timeout=10
            )

            if token_response.status_code != 200:
                logger.error("Keycloak auth failed: %s", token_response.text)
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            keycloak_tokens = token_response.json()
            access_token = keycloak_tokens.get("access_token")
            id_token = keycloak_tokens.get("id_token")

            request.session["oidc_id_token"] = id_token

            userinfo_response = requests.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
                verify=verify_ssl,
                timeout=10,
            )

            if userinfo_response.status_code != 200:
                logger.error("Keycloak userinfo failed: %s", userinfo_response.text)
                return Response(
                    {"error": "Error retrieving user information"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            userinfo = userinfo_response.json()

            keycloak_username = userinfo.get("preferred_username", username)
            email = userinfo.get("email", "")
            first_name = userinfo.get("given_name", "")
            last_name = userinfo.get("family_name", "")

            user, created = User.objects.get_or_create(
                username=keycloak_username,
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

            django_token, _ = Token.objects.get_or_create(user=user)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            return Response(
                {
                    "token": django_token.key,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "keycloak_access_token": access_token,
                    "keycloak_id_token": id_token,
                    "keycloak_refresh_token": keycloak_tokens.get("refresh_token"),
                    "expires_in": keycloak_tokens.get("expires_in"),
                },
                status=status.HTTP_200_OK,
            )

        except requests.exceptions.RequestException as e:
            logger.exception("Keycloak connection error: %s", str(e), exc_info=True)
            return Response(
                {"error": "Keycloak connection error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception("Keycloak authentication error: %s", str(e), exc_info=True)
            return Response(
                {"error": "Error during authentication."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KeycloakRegisterAPIView(APIView):
    """API view for registering new users via Keycloak Admin REST API."""

    throttle_classes = [IPBasedThrottle]

    @swagger_auto_schema(
        operation_description="Register a new user in Keycloak",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "email", "password"],
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email address"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="First name (optional)"
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Last name (optional)"
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Missing required fields or invalid data"
            ),
            409: openapi.Response(description="User already exists in Keycloak"),
            500: openapi.Response(
                description="Keycloak configuration missing or connection error"
            ),
        },
    )
    def post(self, request):
        """Handle POST request for user registration via Keycloak."""
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()

        if not username or not email or not password:
            return Response(
                {"error": "Username, email, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        keycloak_config = _get_keycloak_config()

        token_url = keycloak_config.get("ACCESS_TOKEN_URL")
        keycloak_client_id = keycloak_config.get("CLIENT_ID")
        keycloak_client_secret = keycloak_config.get("SECRET")
        issuer = keycloak_config.get("ID_TOKEN_ISSUER")
        verify_ssl = keycloak_config.get("VERIFY_SSL", True)

        if not all([token_url, keycloak_client_id, keycloak_client_secret, issuer]):
            return Response(
                {"error": "Keycloak configuration missing."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        base_url, realm = _get_keycloak_admin_base_url(issuer)
        if not base_url or not realm:
            return Response(
                {"error": "Unable to determine Keycloak admin URL from issuer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # 1. Obtain a service account token via client_credentials grant
            admin_token_data = {
                "grant_type": "client_credentials",
                "client_id": keycloak_client_id,
                "client_secret": keycloak_client_secret,
            }
            admin_token_response = requests.post(
                token_url, data=admin_token_data, verify=verify_ssl, timeout=10
            )

            if admin_token_response.status_code != 200:
                logger.error(
                    "Failed to obtain Keycloak admin token: %s",
                    admin_token_response.text,
                )
                return Response(
                    {"error": "Failed to obtain admin access to Keycloak."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            admin_access_token = admin_token_response.json().get("access_token")

            # 2. Create user in Keycloak via Admin REST API
            admin_users_url = f"{base_url}/admin/realms/{realm}/users"

            user_payload = {
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": False,
                "credentials": [
                    {
                        "type": "password",
                        "value": password,
                        "temporary": False,
                    }
                ],
            }

            create_response = requests.post(
                admin_users_url,
                json=user_payload,
                headers={
                    "Authorization": f"Bearer {admin_access_token}",
                    "Content-Type": "application/json",
                },
                verify=verify_ssl,
                timeout=10,
            )

            if create_response.status_code == 409:
                return Response(
                    {"error": "A user with this username or email already exists."},
                    status=status.HTTP_409_CONFLICT,
                )

            if create_response.status_code not in (201, 204):
                error_detail = ""
                try:
                    error_detail = create_response.json().get(
                        "errorMessage", create_response.text
                    )
                except Exception:
                    error_detail = create_response.text
                logger.error(
                    "Keycloak user creation failed (HTTP %s): %s",
                    create_response.status_code,
                    error_detail,
                )
                return Response(
                    {
                        "error": "Failed to create user in Keycloak.",
                        "detail": error_detail,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # 3. Create corresponding Django user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )

            if created:
                try:
                    anonymous_group, _ = Group.objects.get_or_create(name="anonymous")
                    registered_group, _ = Group.objects.get_or_create(
                        name="registered-members"
                    )
                    user.groups.add(anonymous_group, registered_group)
                    logger.info(
                        "Groups 'anonymous' and 'registered-members' "
                        "assigned to user %s",
                        username,
                    )
                except Exception as e:
                    logger.exception(
                        "Error assigning groups to user %s: %s",
                        username,
                        str(e),
                        exc_info=True,
                    )

            return Response(
                {
                    "message": "User registered successfully.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except requests.exceptions.RequestException as e:
            logger.exception("Keycloak connection error: %s", str(e), exc_info=True)
            return Response(
                {"error": "Keycloak connection error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception("Keycloak registration error: %s", str(e), exc_info=True)
            return Response(
                {"error": "Error during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KeycloakTokenRefreshAPIView(APIView):
    """API view for refreshing Keycloak access tokens."""

    throttle_classes = [IPBasedThrottle]

    @swagger_auto_schema(
        operation_description="Refresh Keycloak access token using a refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh_token"],
            properties={
                "refresh_token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Keycloak refresh token",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "keycloak_access_token": openapi.Schema(
                            type=openapi.TYPE_STRING
                        ),
                        "keycloak_refresh_token": openapi.Schema(
                            type=openapi.TYPE_STRING
                        ),
                        "keycloak_id_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "expires_in": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "token": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Django authentication token",
                        ),
                    },
                ),
            ),
            400: openapi.Response(description="Refresh token is required"),
            401: openapi.Response(description="Invalid or expired refresh token"),
            500: openapi.Response(
                description="Keycloak configuration missing or connection error"
            ),
        },
    )
    def post(self, request):
        """Handle POST request for token refresh via Keycloak."""
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        keycloak_config = _get_keycloak_config()

        token_url = keycloak_config.get("ACCESS_TOKEN_URL")
        userinfo_url = keycloak_config.get("PROFILE_URL")
        keycloak_client_id = keycloak_config.get("CLIENT_ID")
        keycloak_client_secret = keycloak_config.get("SECRET")
        verify_ssl = keycloak_config.get("VERIFY_SSL", True)

        if not all([token_url, keycloak_client_id]):
            return Response(
                {"error": "Keycloak configuration missing."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        token_data = {
            "grant_type": "refresh_token",
            "client_id": keycloak_client_id,
            "refresh_token": refresh_token,
        }

        if keycloak_client_secret:
            token_data["client_secret"] = keycloak_client_secret

        try:
            token_response = requests.post(
                token_url, data=token_data, verify=verify_ssl, timeout=10
            )

            if token_response.status_code != 200:
                logger.error("Keycloak token refresh failed: %s", token_response.text)
                return Response(
                    {"error": "Invalid or expired refresh token."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            keycloak_tokens = token_response.json()
            access_token = keycloak_tokens.get("access_token")
            new_id_token = keycloak_tokens.get("id_token")

            # Store the new id_token in session for logout
            if hasattr(request, "session"):
                request.session["oidc_id_token"] = new_id_token

            # Fetch user info to sync Django user
            response_data = {
                "keycloak_access_token": access_token,
                "keycloak_refresh_token": keycloak_tokens.get("refresh_token"),
                "keycloak_id_token": new_id_token,
                "expires_in": keycloak_tokens.get("expires_in"),
            }

            if userinfo_url:
                userinfo_response = requests.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    verify=verify_ssl,
                    timeout=10,
                )

                if userinfo_response.status_code == 200:
                    userinfo = userinfo_response.json()
                    username = userinfo.get("preferred_username", "")

                    if username:
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                "email": userinfo.get("email", ""),
                                "first_name": userinfo.get("given_name", ""),
                                "last_name": userinfo.get("family_name", ""),
                            },
                        )

                        if not created:
                            email = userinfo.get("email", "")
                            first_name = userinfo.get("given_name", "")
                            last_name = userinfo.get("family_name", "")
                            if email:
                                user.email = email
                            if first_name:
                                user.first_name = first_name
                            if last_name:
                                user.last_name = last_name
                            user.save()

                        django_token, _ = Token.objects.get_or_create(user=user)
                        response_data["token"] = django_token.key
                        response_data["user"] = {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        }

            return Response(response_data, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            logger.exception("Keycloak connection error: %s", str(e), exc_info=True)
            return Response(
                {"error": "Keycloak connection error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception("Keycloak token refresh error: %s", str(e), exc_info=True)
            return Response(
                {"error": "Error during token refresh."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChangePasswordAPIView(APIView):
    """API view for allowing authenticated users to change their password."""

    throttle_classes = [IPBasedThrottle]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change authenticated user's password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["old_password", "new_password", "new_password_confirm"],
            properties={
                "old_password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Current password"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="New password"
                ),
                "new_password_confirm": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Confirm new password"
                ),
            },
        ),
        responses={
            200: openapi.Response(description="Password changed successfully"),
            400: openapi.Response(description="Validation error"),
            401: openapi.Response(description="Authentication required"),
        },
    )
    def post(self, request):
        user = request.user

        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")
        new_password_confirm = request.data.get("new_password_confirm", "")

        if not old_password or not new_password or not new_password_confirm:
            return Response(
                {
                    "error": "old_password, new_password and new_password_confirm are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != new_password_confirm:
            return Response(
                {"error": "New password and confirmation do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Attempt Keycloak synchronization if configuration is present
        try:
            keycloak_config = _get_keycloak_config()
            token_url = keycloak_config.get("ACCESS_TOKEN_URL")
            keycloak_client_id = keycloak_config.get("CLIENT_ID")
            keycloak_client_secret = keycloak_config.get("SECRET")
            issuer = keycloak_config.get("ID_TOKEN_ISSUER")
            verify_ssl = keycloak_config.get("VERIFY_SSL", True)

            if token_url and keycloak_client_id and keycloak_client_secret and issuer:

                token_data = {
                    "grant_type": "password",
                    "client_id": keycloak_client_id,
                    "username": user.username,
                    "password": old_password,
                    "scope": "openid profile email",
                }

                if keycloak_client_secret:
                    token_data["client_secret"] = keycloak_client_secret

                token_response = requests.post(
                    token_url, data=token_data, verify=verify_ssl, timeout=10
                )
                if not token_response.ok:
                    return Response(
                        {"error": "Old password is incorrect."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                base_url, realm = _get_keycloak_admin_base_url(issuer)
                if not base_url or not realm:
                    return Response(
                        {
                            "error": "Unable to determine Keycloak admin URL from issuer."
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # 1) obtain admin token via client_credentials
                admin_token_data = {
                    "grant_type": "client_credentials",
                    "client_id": keycloak_client_id,
                    "client_secret": keycloak_client_secret,
                }
                admin_token_response = requests.post(
                    token_url, data=admin_token_data, verify=verify_ssl, timeout=10
                )

                if admin_token_response.status_code != 200:
                    logger.error(
                        "Failed to obtain Keycloak admin token: %s",
                        admin_token_response.text,
                    )
                    return Response(
                        {"error": "Failed to obtain admin access to Keycloak."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                admin_access_token = admin_token_response.json().get("access_token")

                # 2) find user in Keycloak
                admin_users_search_url = f"{base_url}/admin/realms/{realm}/users"
                params = {"username": user.username}
                users_resp = requests.get(
                    admin_users_search_url,
                    params=params,
                    headers={"Authorization": f"Bearer {admin_access_token}"},
                    verify=verify_ssl,
                    timeout=10,
                )

                if users_resp.status_code != 200:
                    logger.error("Failed to search Keycloak user: %s", users_resp.text)
                    return Response(
                        {"error": "Failed to locate user in Keycloak."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                users_list = users_resp.json()
                if not users_list:
                    logger.warning(
                        "User %s not found in Keycloak - aborting sync", user.username
                    )
                    return Response(
                        {"error": "User not found in Keycloak."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                kc_user = users_list[0]
                kc_user_id = kc_user.get("id")

                if not kc_user_id:
                    logger.error(
                        "Keycloak user id missing in response for %s", user.username
                    )
                    return Response(
                        {"error": "Invalid response from Keycloak user search."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # 3) reset Keycloak password
                reset_url = (
                    f"{base_url}/admin/realms/{realm}/users/{kc_user_id}/reset-password"
                )
                reset_payload = {
                    "type": "password",
                    "value": new_password,
                    "temporary": False,
                }
                reset_resp = requests.put(
                    reset_url,
                    json=reset_payload,
                    headers={
                        "Authorization": f"Bearer {admin_access_token}",
                        "Content-Type": "application/json",
                    },
                    verify=verify_ssl,
                    timeout=10,
                )

                if reset_resp.status_code not in (200, 204):
                    logger.error(
                        "Failed to reset Keycloak password: %s", reset_resp.text
                    )
                    return Response(
                        {"error": "Failed to reset password in Keycloak."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # 4) terminate Keycloak sessions for the user to force re-login
                try:
                    sessions_url = (
                        f"{base_url}/admin/realms/{realm}/users/{kc_user_id}/sessions"
                    )
                    requests.delete(
                        sessions_url,
                        headers={"Authorization": f"Bearer {admin_access_token}"},
                        verify=verify_ssl,
                        timeout=10,
                    )
                except Exception:
                    logger.exception(
                        "Failed to delete Keycloak sessions for user %s", user.username
                    )

        except requests.exceptions.RequestException as e:
            logger.exception(
                "Keycloak connection error while changing password: %s",
                str(e),
                exc_info=True,
            )
            return Response(
                {"error": "Keycloak connection error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception(
                "Unexpected error during Keycloak sync: %s", str(e), exc_info=True
            )
            return Response(
                {"error": "Error during Keycloak synchronization."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # If we reached here, Keycloak was updated (or sync not configured). Update Django password
        try:
            user.set_password(new_password)
            user.save()

            # Invalidate existing tokens and issue a fresh one
            Token.objects.filter(user=user).delete()
            new_token = Token.objects.create(user=user)

            return Response(
                {"message": "Password changed successfully.", "token": new_token.key},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(
                "Error changing password in Django: %s", str(e), exc_info=True
            )
            return Response(
                {"error": "Error changing password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class KeycloakLogoutView(View):
    """View for handling Keycloak logout."""

    @swagger_auto_schema(
        operation_description="Logout user from Keycloak and Django session",
        responses={
            302: openapi.Response(
                description="Redirect to Keycloak " "logout or logout complete page"
            ),
        },
    )
    def get(self, request):
        """Handle GET request for logout."""

        logger.debug("=" * 80)
        logger.debug("KEYCLOAK LOGOUT - CHIAMATA RICEVUTA")
        logger.debug("=" * 80)

        try:
            keycloak_config = _get_keycloak_config()

            logger.debug(f"Keycloak config trovata: {bool(keycloak_config)}")

            id_token = request.session.get("oidc_id_token")

            if keycloak_config:
                issuer = keycloak_config.get("ID_TOKEN_ISSUER")
                client_id = keycloak_config.get("CLIENT_ID", "")

                logger.debug(f"Issuer: {issuer}")
                logger.debug(f"Client ID: {client_id}")

                if issuer:
                    django_logout_url = request.build_absolute_uri(
                        "/account/logout/complete/"
                    )

                    keycloak_logout_url = f"{issuer}/protocol/openid-connect/logout"
                    params = {
                        "post_logout_redirect_uri": django_logout_url,
                        "client_id": client_id,
                    }

                    if id_token:
                        params["id_token_hint"] = id_token

                    logout_url = f"{keycloak_logout_url}?{urlencode(params)}"
                    logger.debug(f"Redirect a Keycloak: {logout_url}")
                    logger.debug("=" * 80)

                    requests.get(keycloak_logout_url, params=params, timeout=10)

                    logout(request)
                    return redirect("/account/logout/complete/")

            logger.debug("Keycloak non configurato - logout solo Django")
            logger.debug("=" * 80)
            logout(request)
            return redirect("/account/logout/complete/")

        except Exception as e:
            logger.exception("ERRORE durante logout: %s", str(e), exc_info=True)

            traceback.print_exc()
            logout(request)
            return redirect("/")


class KeycloakLogoutCompleteView(View):
    """View for completing logout and redirecting."""

    @swagger_auto_schema(
        operation_description="Complete logout process and redirect to homepage or specified URL",
        manual_parameters=[
            openapi.Parameter(
                "next",
                openapi.IN_QUERY,
                description="URL to redirect after logout",
                type=openapi.TYPE_STRING,
                required=False,
            )
        ],
        responses={
            302: openapi.Response(description="Redirect to homepage or next URL"),
        },
    )
    def get(self, request):
        """Handle GET request for completing logout."""
        logger.debug("=" * 80)
        logger.debug("LOGOUT COMPLETATO - Redirect a homepage")
        logger.debug("=" * 80)

        if request.user.is_authenticated:
            logout(request)

        next_url = request.GET.get("next", "/")
        allowed_hosts = {request.get_host()}
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=allowed_hosts):
            return redirect(next_url)
        else:
            return redirect("/")
