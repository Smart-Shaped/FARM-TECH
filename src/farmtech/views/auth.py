"""
Keycloak authentication API view for FarmTech application.
"""

import logging
from urllib.parse import urlencode
import traceback
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, logout
from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from django.utils.http import url_has_allowed_host_and_scheme
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from farmtech.throttles import IPBasedThrottle


logger = logging.getLogger(__name__)
User = get_user_model()


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

        keycloak_config = getattr(settings, "SOCIALACCOUNT_PROVIDERS_DEFS", {}).get(
            "keycloak", {}
        )

        if not keycloak_config:
            keycloak_config = getattr(settings, "_KEYCLOAK_SOCIALACCOUNT_PROVIDER", {})

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

        print("=" * 80)
        print("KEYCLOAK LOGOUT - CHIAMATA RICEVUTA")
        print("=" * 80)

        try:
            keycloak_config = getattr(settings, "SOCIALACCOUNT_PROVIDERS_DEFS", {}).get(
                "keycloak", {}
            )

            if not keycloak_config:
                keycloak_config = getattr(
                    settings, "_KEYCLOAK_SOCIALACCOUNT_PROVIDER", {}
                )

            print(f"Keycloak config trovata: {bool(keycloak_config)}")

            if keycloak_config:
                issuer = keycloak_config.get("ID_TOKEN_ISSUER")
                client_id = keycloak_config.get("CLIENT_ID", "")

                print(f"Issuer: {issuer}")
                print(f"Client ID: {client_id}")

                if issuer:
                    django_logout_url = request.build_absolute_uri(
                        "/account/logout/complete/"
                    )

                    keycloak_logout_url = f"{issuer}/protocol/openid-connect/logout"
                    params = {
                        "post_logout_redirect_uri": django_logout_url,
                        "client_id": client_id,
                    }

                    logout_url = f"{keycloak_logout_url}?{urlencode(params)}"
                    print(f"Redirect a Keycloak: {logout_url}")
                    print("=" * 80)

                    logout(request)
                    return redirect(logout_url)

            print("Keycloak non configurato - logout solo Django")
            print("=" * 80)
            logout(request)
            return redirect("/account/logout/complete/")

        except Exception as e:
            print(f"ERRORE durante logout: {str(e)}")

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
        print("=" * 80)
        print("LOGOUT COMPLETATO - Redirect a homepage")
        print("=" * 80)

        if request.user.is_authenticated:
            logout(request)

        next_url = request.GET.get("next", "/")
        allowed_hosts = {request.get_host()}
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=allowed_hosts):
            return redirect(next_url)
        else:
            return redirect("/")
