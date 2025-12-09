"""
Unit tests for dashboard views.
Tests for PublishDashboardAPIView.
"""

from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import Http404

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class PublishDashboardAPIViewTestCase(TestCase):
    """Tests for PublishDashboardAPIView using APIClient with force_authenticate."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testdashboarduser",
            password="testpassword",
            email="testdashboard@example.com",
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.dashboard.get_object_or_404")
    def test_patch_dashboard_not_found(self, mock_get_object):
        """Test PATCH request for non-existent dashboard returns 404."""

        mock_get_object.side_effect = Http404()

        response = self.client.patch("/api/dashboard/999/publish/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dashboard.GeoApp")
    @patch("farmtech.views.dashboard.get_object_or_404")
    @patch("farmtech.views.dashboard.PublishDashboardAPIView.check_object_permissions")
    def test_patch_publish_unpublished_dashboard(
        self, mock_check_perms, mock_get_object, mock_geoapp_class
    ):
        """Test PATCH request to publish an unpublished dashboard."""
        # Mock permission check to pass
        mock_check_perms.return_value = None

        # Create mock dashboard
        mock_dashboard = MagicMock()
        mock_dashboard.pk = 1
        mock_dashboard.id = 1
        mock_dashboard.is_approved = False
        mock_dashboard.is_published = False
        mock_dashboard.advertised = False
        mock_dashboard.group = MagicMock()
        mock_get_object.return_value = mock_dashboard

        # Create mock for other dashboards in group
        mock_geoapp_class.objects.filter.return_value.exclude.return_value.all.return_value = (
            []
        )

        response = self.client.patch("/api/dashboard/1/publish/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Dashboard successfully published.")
        self.assertTrue(response.data["is_published"])
        mock_dashboard.save.assert_called()

    @patch("farmtech.views.dashboard.get_object_or_404")
    @patch("farmtech.views.dashboard.PublishDashboardAPIView.check_object_permissions")
    def test_patch_already_published_dashboard(self, mock_check_perms, mock_get_object):
        """Test PATCH request for already published dashboard."""
        mock_check_perms.return_value = None

        mock_dashboard = MagicMock()
        mock_dashboard.pk = 1
        mock_dashboard.is_approved = True  # Already approved means already published
        mock_get_object.return_value = mock_dashboard

        response = self.client.patch("/api/dashboard/1/publish/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Dashboard is already published.")
        self.assertTrue(response.data["is_published"])

    @patch("farmtech.views.dashboard.GeoApp")
    @patch("farmtech.views.dashboard.get_object_or_404")
    @patch("farmtech.views.dashboard.PublishDashboardAPIView.check_object_permissions")
    def test_patch_unpublishes_other_dashboards_in_group(
        self, mock_check_perms, mock_get_object, mock_geoapp_class
    ):
        """Test PATCH request unpublishes other dashboards in the same group."""
        mock_check_perms.return_value = None

        # Create mock dashboard to publish
        mock_dashboard = MagicMock()
        mock_dashboard.pk = 1
        mock_dashboard.id = 1
        mock_dashboard.is_approved = False
        mock_dashboard.group = MagicMock()
        mock_get_object.return_value = mock_dashboard

        # Create mock for other dashboard in same group
        other_dashboard = MagicMock()
        other_dashboard.id = 2
        other_dashboard.is_published = True
        other_dashboard.is_approved = True

        mock_geoapp_class.objects.filter.return_value.exclude.return_value.all.return_value = [
            other_dashboard
        ]

        response = self.client.patch("/api/dashboard/1/publish/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify other dashboard was unpublished
        other_dashboard.save.assert_called()

    @patch("farmtech.views.dashboard.get_object_or_404")
    @patch("farmtech.views.dashboard.PublishDashboardAPIView.check_object_permissions")
    def test_patch_permission_denied(self, mock_check_perms, mock_get_object):
        """Test PATCH request with permission denied."""

        mock_dashboard = MagicMock()
        mock_dashboard.pk = 1
        mock_dashboard.group = MagicMock()
        mock_get_object.return_value = mock_dashboard
        mock_check_perms.side_effect = PermissionDenied()

        response = self.client.patch("/api/dashboard/1/publish/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
