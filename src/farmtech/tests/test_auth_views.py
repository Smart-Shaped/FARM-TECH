"""
Unit tests for authentication views.
Tests for KeycloakAuthAPIView, KeycloakLogoutView, and KeycloakLogoutCompleteView.
"""

from unittest.mock import patch, MagicMock
import requests
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from farmtech.views.auth import (
    KeycloakAuthAPIView,
    KeycloakLogoutView,
    KeycloakLogoutCompleteView,
)

User = get_user_model()


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class KeycloakAuthAPIViewTestCase(APITestCase):
    """Tests for KeycloakAuthAPIView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.url = "/api/auth/keycloak/"
        self.factory = RequestFactory()
        self.view = KeycloakAuthAPIView.as_view()

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    def test_post_missing_username(self):
        """Test POST request without username returns 400."""
        request = self.factory.post(
            "/api/auth/keycloak/",
            {"password": "testpassword"},
            content_type="application/json",
        )
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    def test_post_missing_password(self):
        """Test POST request without password returns 400."""
        request = self.factory.post(
            "/api/auth/keycloak/",
            {"username": "testuser"},
            content_type="application/json",
        )
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    def test_post_missing_both_credentials(self):
        """Test POST request without any credentials returns 400."""
        request = self.factory.post(
            "/api/auth/keycloak/", {}, content_type="application/json"
        )
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Username and password are required.")

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth.settings")
    def test_post_missing_keycloak_config(self, mock_settings):
        """Test POST request with missing Keycloak configuration returns 500."""
        mock_settings.SOCIALACCOUNT_PROVIDERS_DEFS = {}
        # Use configure_mock to set the attribute
        mock_settings.configure_mock(**{"_KEYCLOAK_SOCIALACCOUNT_PROVIDER": {}})

        request = self.factory.post(
            "/api/auth/keycloak/",
            {"username": "testuser", "password": "testpassword"},
            content_type="application/json",
        )
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth.requests.post")
    @patch("farmtech.views.auth.settings")
    def test_post_invalid_credentials(self, mock_settings, mock_requests_post):
        """Test POST request with invalid credentials returns 401."""
        mock_settings.SOCIALACCOUNT_PROVIDERS_DEFS = {
            "keycloak": {
                "ACCESS_TOKEN_URL": "http://keycloak.test/token",
                "PROFILE_URL": "http://keycloak.test/userinfo",
                "CLIENT_ID": "test-client",
                "SECRET": "test-secret",
                "VERIFY_SSL": False,
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mock_requests_post.return_value = mock_response

        request = self.factory.post(
            "/api/auth/keycloak/",
            {"username": "testuser", "password": "wrongpassword"},
            content_type="application/json",
        )
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Invalid credentials")

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth.requests.get")
    @patch("farmtech.views.auth.requests.post")
    @patch("farmtech.views.auth.settings")
    def test_post_successful_authentication(
        self, mock_settings, mock_requests_post, mock_requests_get
    ):
        """Test POST request with valid credentials returns 200 and token."""
        mock_settings.SOCIALACCOUNT_PROVIDERS_DEFS = {
            "keycloak": {
                "ACCESS_TOKEN_URL": "http://keycloak.test/token",
                "PROFILE_URL": "http://keycloak.test/userinfo",
                "CLIENT_ID": "test-client",
                "SECRET": "test-secret",
                "VERIFY_SSL": False,
            }
        }

        # Mock token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_requests_post.return_value = mock_token_response

        # Mock userinfo response
        mock_userinfo_response = MagicMock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "preferred_username": "keycloak_testuser",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
        }
        mock_requests_get.return_value = mock_userinfo_response

        request = self.factory.post(
            "/api/auth/keycloak/",
            {"username": "testuser", "password": "testpassword"},
            content_type="application/json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertIn("keycloak_access_token", response.data)
        self.assertEqual(response.data["user"]["username"], "keycloak_testuser")

    @patch.object(KeycloakAuthAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth.requests.post")
    @patch("farmtech.views.auth.settings")
    def test_post_keycloak_connection_error(self, mock_settings, mock_requests_post):
        """Test POST request with Keycloak connection error returns 500."""

        mock_settings.SOCIALACCOUNT_PROVIDERS_DEFS = {
            "keycloak": {
                "ACCESS_TOKEN_URL": "http://keycloak.test/token",
                "PROFILE_URL": "http://keycloak.test/userinfo",
                "CLIENT_ID": "test-client",
                "SECRET": "test-secret",
                "VERIFY_SSL": False,
            }
        }

        mock_requests_post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        request = self.factory.post(
            "/api/auth/keycloak/",
            {"username": "testuser", "password": "testpassword"},
            content_type="application/json",
        )
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Keycloak connection error.")


class KeycloakLogoutViewTestCase(TestCase):
    """Tests for KeycloakLogoutView."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.view = KeycloakLogoutView.as_view()
        self.user = User.objects.create_user(
            username="testlogoutuser",
            password="testpassword",
            email="testlogout@example.com",
        )

    def _add_session_to_request(self, request):
        """Add a proper session to the request."""
        session = SessionStore()
        session.create()
        request.session = session

    @patch("farmtech.views.auth.logout")
    @patch("farmtech.views.auth.settings")
    def test_logout_without_keycloak_config(self, mock_settings, mock_logout):
        """Test logout redirects to local logout when Keycloak is not configured."""
        mock_settings.SOCIALACCOUNT_PROVIDERS_DEFS = {}
        mock_settings.configure_mock(**{"_KEYCLOAK_SOCIALACCOUNT_PROVIDER": {}})

        request = self.factory.get("/account/logout/")
        request.user = self.user
        self._add_session_to_request(request)

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/logout/complete/")
        mock_logout.assert_called_once()

    @patch("farmtech.views.auth.logout")
    @patch("farmtech.views.auth.settings")
    def test_logout_with_keycloak_config(self, mock_settings, mock_logout):
        """Test logout redirects to Keycloak when configured."""
        mock_settings.SOCIALACCOUNT_PROVIDERS_DEFS = {
            "keycloak": {
                "ID_TOKEN_ISSUER": "http://keycloak.test/realms/test",
                "CLIENT_ID": "test-client",
            }
        }

        request = self.factory.get("/account/logout/")
        request.user = self.user
        self._add_session_to_request(request)
        request.build_absolute_uri = MagicMock(
            return_value="http://testserver/account/logout/complete/"
        )

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("keycloak.test", response.url)
        self.assertIn("logout", response.url)
        mock_logout.assert_called_once()


class KeycloakLogoutCompleteViewTestCase(TestCase):
    """Tests for KeycloakLogoutCompleteView."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.view = KeycloakLogoutCompleteView.as_view()
        self.user = User.objects.create_user(
            username="testlogoutcomplete",
            password="testpassword",
            email="testlogoutcomplete@example.com",
        )

    def _add_session_to_request(self, request):
        """Add a proper session to the request."""
        session = SessionStore()
        session.create()
        request.session = session

    @patch("farmtech.views.auth.logout")
    def test_logout_complete_redirects_to_homepage(self, mock_logout):
        """Test logout complete redirects to homepage by default."""
        request = self.factory.get("/account/logout/complete/")
        request.user = MagicMock(is_authenticated=False)
        self._add_session_to_request(request)

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    @patch("farmtech.views.auth.logout")
    def test_logout_complete_redirects_to_next_url(self, mock_logout):
        """Test logout complete redirects to 'next' parameter if safe."""
        request = self.factory.get("/account/logout/complete/", {"next": "/dashboard/"})
        request.user = MagicMock(is_authenticated=False)
        self._add_session_to_request(request)

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")

    @patch("farmtech.views.auth.logout")
    def test_logout_complete_ignores_unsafe_next_url(self, mock_logout):
        """Test logout complete ignores unsafe 'next' parameter."""
        request = self.factory.get(
            "/account/logout/complete/", {"next": "http://malicious.com/"}
        )
        request.user = MagicMock(is_authenticated=False)
        self._add_session_to_request(request)

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    @patch("farmtech.views.auth.logout")
    def test_logout_complete_logs_out_authenticated_user(self, mock_logout):
        """Test logout complete logs out authenticated user."""
        request = self.factory.get("/account/logout/complete/")
        request.user = self.user
        self._add_session_to_request(request)

        response = self.view(request)
        mock_logout.assert_called_once_with(request)
        self.assertEqual(response.status_code, 302)
