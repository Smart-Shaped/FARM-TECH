"""
Unit tests for group views.
Tests for GroupJoinRequestAPIView and GroupProfileListAPIView.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from farmtech.serializers import GroupJoinRequestSerializer

User = get_user_model()


class GroupJoinRequestAPIViewTestCase(TestCase):
    """Tests for GroupJoinRequestAPIView using APIClient with force_authenticate."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.group.GroupJoinRequestAPIView.throttle_classes", [])
    def test_post_invalid_data_missing_fields(self):
        """Test POST request with missing fields returns 400."""
        response = self.client.post(
            "/api/group/group-join-request/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("farmtech.views.group.GroupJoinRequestAPIView.throttle_classes", [])
    def test_post_invalid_motivation_too_short(self):
        """Test POST request with motivation less than 10 characters returns 400."""
        response = self.client.post(
            "/api/group/group-join-request/",
            {
                "group_profile_id": 1,
                "requested_role": "member",
                "motivation": "short",  # Less than 10 chars
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("farmtech.views.group.GroupJoinRequestAPIView.throttle_classes", [])
    def test_post_invalid_requested_role(self):
        """Test POST request with invalid role returns 400."""
        response = self.client.post(
            "/api/group/group-join-request/",
            {
                "group_profile_id": 1,
                "requested_role": "admin",  # Invalid role
                "motivation": "I want to join this group because it's great",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("farmtech.views.group.GroupProfile")
    @patch("farmtech.views.group.GroupJoinRequestAPIView.throttle_classes", [])
    def test_post_group_not_found(self, mock_group_profile_class):
        """Test POST request for non-existent group returns 404."""
        mock_group_profile_class.DoesNotExist = Exception
        mock_group_profile_class.objects.get.side_effect = (
            mock_group_profile_class.DoesNotExist()
        )

        response = self.client.post(
            "/api/group/group-join-request/",
            {
                "group_profile_id": 999,
                "requested_role": "member",
                "motivation": "I want to join this group because it's great",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GroupProfileListAPIViewTestCase(TestCase):
    """Tests for GroupProfileListAPIView using APIClient."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testlistuser",
            password="testpassword",
            email="testlist@example.com",
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.group.GroupProfile")
    def test_get_empty_group_list(self, mock_group_profile_class):
        """Test GET request returns empty list when no groups."""
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = []
        mock_group_profile_class.objects.all.return_value = mock_queryset

        response = self.client.get("/api/group/list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("farmtech.views.group.GeoApp")
    @patch("farmtech.views.group.GroupMember")
    @patch("farmtech.views.group.GroupProfile")
    def test_get_group_list_with_groups(
        self, mock_group_profile_class, mock_group_member_class, mock_geoapp_class
    ):
        """Test GET request returns list of groups."""
        mock_group = MagicMock()
        mock_group.id = 1
        mock_group.title = "Test Group"
        mock_group.slug = "test-group"
        mock_group.description = "Test description"
        mock_group.access = "public"
        mock_group.email = "test@example.com"
        mock_group.logo = None
        mock_group.created = None
        mock_group.last_modified = None
        mock_group.group = MagicMock()
        mock_group.group.id = 1

        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = [mock_group]
        mock_group_profile_class.objects.all.return_value = mock_queryset

        # Mock GroupMember.objects.filter().count()
        mock_group_member_class.objects.filter.return_value.count.return_value = 5

        # Mock GeoApp.objects.filter().first()
        mock_geoapp_class.objects.filter.return_value.first.return_value = None

        response = self.client.get("/api/group/list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("farmtech.views.group.GroupProfile")
    def test_get_group_list_database_error(self, mock_group_profile_class):
        """Test GET request handles database errors."""
        mock_group_profile_class.objects.all.side_effect = Exception("Database error")

        response = self.client.get("/api/group/list/")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupJoinRequestSerializerTestCase(TestCase):
    """Tests for GroupJoinRequestSerializer validation."""

    def test_valid_data(self):
        """Test serializer accepts valid data."""

        data = {
            "group_profile_id": 1,
            "requested_role": "member",
            "motivation": "I want to join this group because it's relevant to my work",
        }
        serializer = GroupJoinRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_group_profile_id(self):
        """Test serializer rejects missing group_profile_id."""

        data = {
            "requested_role": "member",
            "motivation": "I want to join this group",
        }
        serializer = GroupJoinRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("group_profile_id", serializer.errors)

    def test_motivation_too_short(self):
        """Test serializer rejects motivation shorter than 10 characters."""

        data = {
            "group_profile_id": 1,
            "requested_role": "member",
            "motivation": "short",
        }
        serializer = GroupJoinRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("motivation", serializer.errors)

    def test_invalid_role(self):
        """Test serializer rejects invalid role."""

        data = {
            "group_profile_id": 1,
            "requested_role": "superadmin",
            "motivation": "I want to join this group because it's great",
        }
        serializer = GroupJoinRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("requested_role", serializer.errors)

    def test_valid_manager_role(self):
        """Test serializer accepts manager role."""

        data = {
            "group_profile_id": 1,
            "requested_role": "manager",
            "motivation": "I want to manage this group because I have experience",
        }
        serializer = GroupJoinRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
