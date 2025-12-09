"""
Unit tests for dataset views.
Tests for DatasetUpdateAPIView, GroupExcelTemplatesAPIView, and DownloadExcelTemplateAPIView.
"""

from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np
from rest_framework import status
from rest_framework.test import APIClient

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from farmtech.views.dataset import _series_to_kwargs
from farmtech.serializers import GroupExcelTemplatesSerializer, DatasetUpdateSerializer

User = get_user_model()


class SeriesToKwargsTestCase(TestCase):
    """Tests for the _series_to_kwargs helper function."""

    def test_handles_missing_values(self):
        """Test that NaN/None values are converted to None."""

        series = pd.Series({"a": np.nan, "b": None, "c": "value"})
        result = _series_to_kwargs(series)

        self.assertIsNone(result["a"])
        self.assertIsNone(result["b"])
        self.assertEqual(result["c"], "value")

    def test_handles_numpy_scalars(self):
        """Test that numpy scalars are converted to Python types."""

        series = pd.Series({"a": np.int64(42), "b": np.float64(3.14)})
        result = _series_to_kwargs(series)

        self.assertEqual(result["a"], 42)
        self.assertIsInstance(result["a"], int)

    def test_float_to_int_conversion(self):
        """Test that float values that are integers are converted to int."""

        series = pd.Series({"a": 42.0, "b": 3.5})
        result = _series_to_kwargs(series)

        self.assertEqual(result["a"], 42)
        self.assertIsInstance(result["a"], int)
        self.assertEqual(result["b"], 3.5)
        self.assertIsInstance(result["b"], float)

    def test_string_stripping(self):
        """Test that string values are stripped."""

        series = pd.Series({"a": "  hello  ", "b": "world"})
        result = _series_to_kwargs(series)

        self.assertEqual(result["a"], "hello")
        self.assertEqual(result["b"], "world")


class DatasetUpdateAPIViewTestCase(TestCase):
    """Tests for DatasetUpdateAPIView using APIClient with force_authenticate."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testdatasetuser",
            password="testpassword",
            email="testdataset@example.com",
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.dataset.DatasetUpdateSerializer")
    @patch("farmtech.views.dataset.DatasetUpdateAPIView.permission_classes", [])
    def test_post_invalid_serializer(self, mock_serializer_class):
        """Test POST request with invalid data returns 400."""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {"dataset_name": ["This field is required."]}
        mock_serializer_class.return_value = mock_serializer

        response = self.client.post("/api/dataset/update/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("farmtech.views.dataset.Dataset")
    @patch("farmtech.views.dataset.DatasetUpdateSerializer")
    @patch("farmtech.views.dataset.DatasetUpdateAPIView.permission_classes", [])
    def test_post_dataset_not_found(self, mock_serializer_class, mock_dataset_class):
        """Test POST request for non-existent dataset returns 404."""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            "dataset_name": "nonexistent_dataset",
            "excel_file": MagicMock(name="test.xlsx"),
        }
        mock_serializer_class.return_value = mock_serializer

        mock_dataset_class.DoesNotExist = Exception
        mock_dataset_class.objects.get.side_effect = mock_dataset_class.DoesNotExist()

        response = self.client.post(
            "/api/dataset/update/",
            {"dataset_name": "nonexistent_dataset"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch("farmtech.views.dataset.Dataset")
    @patch("farmtech.views.dataset.DatasetUpdateSerializer")
    @patch("farmtech.views.dataset.DatasetUpdateAPIView.permission_classes", [])
    def test_post_dataset_experiment_not_found(
        self, mock_serializer_class, mock_dataset_class, mock_dataset_experiment_class
    ):
        """Test POST request when DatasetExperiment not found returns 404."""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            "dataset_name": "test_dataset",
            "excel_file": MagicMock(name="test.xlsx"),
        }
        mock_serializer_class.return_value = mock_serializer

        mock_dataset = MagicMock()
        mock_dataset.name = "test_dataset"
        mock_dataset.id = 1
        mock_dataset_class.objects.get.return_value = mock_dataset

        mock_dataset_experiment_class.DoesNotExist = Exception
        mock_dataset_experiment_class.objects.get.side_effect = (
            mock_dataset_experiment_class.DoesNotExist()
        )

        response = self.client.post(
            "/api/dataset/update/", {"dataset_name": "test_dataset"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GroupExcelTemplatesAPIViewTestCase(TestCase):
    """Tests for GroupExcelTemplatesAPIView using APIClient with force_authenticate."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testtemplatesuser",
            password="testpassword",
            email="testtemplates@example.com",
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.dataset.GroupExcelTemplatesSerializer")
    @patch("farmtech.views.dataset.GroupExcelTemplatesAPIView.permission_classes", [])
    def test_post_invalid_serializer(self, mock_serializer_class):
        """Test POST request with invalid data returns 400."""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {"group_profile_id": ["This field is required."]}
        mock_serializer_class.return_value = mock_serializer

        response = self.client.post("/api/dataset/excel-templates/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("farmtech.views.dataset.GroupProfile")
    @patch("farmtech.views.dataset.GroupExcelTemplatesSerializer")
    @patch("farmtech.views.dataset.GroupExcelTemplatesAPIView.permission_classes", [])
    def test_post_group_not_found(
        self, mock_serializer_class, mock_group_profile_class
    ):
        """Test POST request for non-existent group returns 404."""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"group_profile_id": 999}
        mock_serializer_class.return_value = mock_serializer

        mock_group_profile_class.DoesNotExist = Exception
        mock_group_profile_class.objects.get.side_effect = (
            mock_group_profile_class.DoesNotExist()
        )

        response = self.client.post(
            "/api/dataset/excel-templates/", {"group_profile_id": 999}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch("farmtech.views.dataset.GroupProfile")
    @patch("farmtech.views.dataset.GroupExcelTemplatesSerializer")
    @patch("farmtech.views.dataset.GroupExcelTemplatesAPIView.check_object_permissions")
    @patch("farmtech.views.dataset.GroupExcelTemplatesAPIView.permission_classes", [])
    def test_post_no_datasets_for_group(
        self,
        mock_check_perms,
        mock_serializer_class,
        mock_group_profile_class,
        mock_dataset_experiment_class,
    ):
        """Test POST request for group with no datasets returns 404."""
        mock_check_perms.return_value = None

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"group_profile_id": 1}
        mock_serializer_class.return_value = mock_serializer

        mock_group = MagicMock()
        mock_group.id = 1
        mock_group.title = "Test Group"
        mock_group_profile_class.objects.get.return_value = mock_group

        # Mock queryset that returns empty
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_dataset_experiment_class.objects.filter.return_value.select_related.return_value = (
            mock_queryset
        )

        response = self.client.post(
            "/api/dataset/excel-templates/", {"group_profile_id": 1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dataset.RawFile")
    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch("farmtech.views.dataset.GroupProfile")
    @patch("farmtech.views.dataset.GroupExcelTemplatesSerializer")
    @patch("farmtech.views.dataset.GroupExcelTemplatesAPIView.check_object_permissions")
    @patch("farmtech.views.dataset.GroupExcelTemplatesAPIView.permission_classes", [])
    def test_post_successful_templates_retrieval(
        self,
        mock_check_perms,
        mock_serializer_class,
        mock_group_profile_class,
        mock_dataset_experiment_class,
        mock_raw_file_class,
    ):
        """Test POST request successfully retrieves templates."""
        mock_check_perms.return_value = None

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"group_profile_id": 1}
        mock_serializer_class.return_value = mock_serializer

        mock_group = MagicMock()
        mock_group.id = 1
        mock_group.title = "Test Group"
        mock_group.slug = "test-group"
        mock_group_profile_class.objects.get.return_value = mock_group

        # Mock dataset experiment
        mock_dataset_exp = MagicMock()
        mock_dataset_exp.id = 1
        mock_dataset_exp.template_path = "/path/to/template.xlsx"
        mock_dataset_exp.layer_dataset.name = "Test Dataset"

        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_queryset.__iter__ = lambda self: iter([mock_dataset_exp])
        mock_dataset_experiment_class.objects.filter.return_value.select_related.return_value = (
            mock_queryset
        )

        mock_raw_file_class.objects.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        response = self.client.post(
            "/api/dataset/excel-templates/", {"group_profile_id": 1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["templates_count"], 1)


class DownloadExcelTemplateAPIViewTestCase(TestCase):
    """Tests for DownloadExcelTemplateAPIView using APIClient with force_authenticate."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testdownloaduser",
            password="testpassword",
            email="testdownload@example.com",
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch("farmtech.views.dataset.DownloadExcelTemplateAPIView.permission_classes", [])
    def test_get_dataset_experiment_not_found(self, mock_dataset_experiment_class):
        """Test GET request for non-existent dataset experiment returns 404."""
        mock_dataset_experiment_class.DoesNotExist = Exception
        mock_dataset_experiment_class.objects.select_related.return_value.get.side_effect = (
            mock_dataset_experiment_class.DoesNotExist()
        )

        response = self.client.get("/api/dataset/download-template/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch(
        "farmtech.views.dataset.DownloadExcelTemplateAPIView.check_object_permissions"
    )
    @patch("farmtech.views.dataset.DownloadExcelTemplateAPIView.permission_classes", [])
    def test_get_no_template_configured(
        self, mock_check_perms, mock_dataset_experiment_class
    ):
        """Test GET request for dataset with no template returns 404."""
        mock_check_perms.return_value = None

        mock_dataset_exp = MagicMock()
        mock_dataset_exp.id = 1
        mock_dataset_exp.template_path = None
        mock_dataset_experiment_class.objects.select_related.return_value.get.return_value = (
            mock_dataset_exp
        )

        response = self.client.get("/api/dataset/download-template/1/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dataset.os.path.exists")
    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch(
        "farmtech.views.dataset.DownloadExcelTemplateAPIView.check_object_permissions"
    )
    @patch("farmtech.views.dataset.DownloadExcelTemplateAPIView.permission_classes", [])
    def test_get_template_file_not_found(
        self, mock_check_perms, mock_dataset_experiment_class, mock_exists
    ):
        """Test GET request when template file doesn't exist returns 404."""
        mock_check_perms.return_value = None

        mock_dataset_exp = MagicMock()
        mock_dataset_exp.id = 1
        mock_dataset_exp.template_path = "/path/to/nonexistent.xlsx"
        mock_dataset_experiment_class.objects.select_related.return_value.get.return_value = (
            mock_dataset_exp
        )

        mock_exists.return_value = False

        response = self.client.get("/api/dataset/download-template/1/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("farmtech.views.dataset.os.path.isfile")
    @patch("farmtech.views.dataset.os.path.exists")
    @patch("farmtech.views.dataset.DatasetExperiment")
    @patch(
        "farmtech.views.dataset.DownloadExcelTemplateAPIView.check_object_permissions"
    )
    @patch("farmtech.views.dataset.DownloadExcelTemplateAPIView.permission_classes", [])
    def test_get_invalid_file_extension(
        self, mock_check_perms, mock_dataset_experiment_class, mock_exists, mock_isfile
    ):
        """Test GET request for non-Excel file returns 404."""
        mock_check_perms.return_value = None

        mock_dataset_exp = MagicMock()
        mock_dataset_exp.id = 1
        mock_dataset_exp.template_path = "/path/to/template.pdf"
        mock_dataset_experiment_class.objects.select_related.return_value.get.return_value = (
            mock_dataset_exp
        )

        mock_exists.return_value = True
        mock_isfile.return_value = True

        response = self.client.get("/api/dataset/download-template/1/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DatasetUpdateSerializerValidationTestCase(TestCase):
    """Tests for DatasetUpdateSerializer validation."""

    def test_valid_xlsx_file(self):
        """Test that .xlsx files are accepted."""

        excel_file = SimpleUploadedFile(
            "test_data.xlsx",
            b"mock excel content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        serializer = DatasetUpdateSerializer(
            data={"dataset_name": "test", "excel_file": excel_file}
        )
        self.assertTrue(serializer.is_valid())

    def test_valid_xls_file(self):
        """Test that .xls files are accepted."""

        excel_file = SimpleUploadedFile(
            "test_data.xls",
            b"mock excel content",
            content_type="application/vnd.ms-excel",
        )

        serializer = DatasetUpdateSerializer(
            data={"dataset_name": "test", "excel_file": excel_file}
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_file_extension(self):
        """Test that non-Excel files are rejected."""

        pdf_file = SimpleUploadedFile(
            "test_data.pdf", b"mock pdf content", content_type="application/pdf"
        )

        serializer = DatasetUpdateSerializer(
            data={"dataset_name": "test", "excel_file": pdf_file}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("excel_file", serializer.errors)


class GroupExcelTemplatesSerializerTestCase(TestCase):
    """Tests for GroupExcelTemplatesSerializer validation."""

    def test_valid_group_profile_id(self):
        """Test that valid group_profile_id is accepted."""

        serializer = GroupExcelTemplatesSerializer(data={"group_profile_id": 1})
        self.assertTrue(serializer.is_valid())

    def test_missing_group_profile_id(self):
        """Test that missing group_profile_id is rejected."""

        serializer = GroupExcelTemplatesSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("group_profile_id", serializer.errors)
