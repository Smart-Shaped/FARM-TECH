from unittest.mock import patch
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase

from farmtech.views.auth import ChangePasswordAPIView

User = get_user_model()


@override_settings(
    REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}
)
class ChangePasswordAPIViewTestCase(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = ChangePasswordAPIView.as_view()

    @patch.object(ChangePasswordAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth._get_keycloak_config", return_value={})
    def test_change_password_success(self):
        user = User.objects.create_user(username="testuser", password="oldpass")
        request = self.factory.post(
            "/api/auth/change-password/",
            {
                "old_password": "oldpass",
                "new_password": "newpass",
                "new_password_confirm": "newpass",
            },
            content_type="application/json",
        )
        request.user = user
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("newpass")
        assert "token" in response.data

    @patch.object(ChangePasswordAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth._get_keycloak_config", return_value={})
    def test_change_password_wrong_old(self):
        user = User.objects.create_user(username="testuser2", password="oldpass")
        request = self.factory.post(
            "/api/auth/change-password/",
            {"old_password": "bad", "new_password": "x", "new_password_confirm": "x"},
            content_type="application/json",
        )
        request.user = user
        response = self.view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("error") == "Old password is incorrect."

    @patch.object(ChangePasswordAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth._get_keycloak_config", return_value={})
    def test_change_password_mismatch(self):
        user = User.objects.create_user(username="testuser3", password="oldpass")
        request = self.factory.post(
            "/api/auth/change-password/",
            {
                "old_password": "oldpass",
                "new_password": "a",
                "new_password_confirm": "b",
            },
            content_type="application/json",
        )
        request.user = user
        response = self.view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data.get("error") == "New password and confirmation do not match."
        )

    @patch.object(ChangePasswordAPIView, "throttle_classes", [])
    @patch("farmtech.views.auth._get_keycloak_config", return_value={})
    def test_change_password_unauthenticated(self):
        request = self.factory.post(
            "/api/auth/change-password/",
            {"old_password": "x", "new_password": "y", "new_password_confirm": "y"},
            content_type="application/json",
        )
        request.user = AnonymousUser()
        response = self.view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
