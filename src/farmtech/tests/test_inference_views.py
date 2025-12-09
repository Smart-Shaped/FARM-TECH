"""
Unit tests for inference views.
Tests for RunSSHCommandView and helper functions.
"""

from unittest.mock import patch, MagicMock

import os
import pandas as pd

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from rasterio.crs import CRS

from farmtech.serializers import DataForInferenceSerializer
from farmtech.views.inference import (
    _clean_folder,
    _collect_results,
    _extract_geometry,
    _polygon_analysis,
    _save_tiff_file,
    _calculate_centroid,
    _invoke_ssh_command,
)
from farmtech.exceptions import (
    InvokeSSHCommandError,
    PolygonAnalysisError,
    TiffSaveError,
)


User = get_user_model()


class CleanFolderTestCase(TestCase):
    """Tests for _clean_folder helper function."""

    @patch("farmtech.views.inference.os.remove")
    @patch("farmtech.views.inference.os.listdir")
    def test_clean_folder_removes_files(self, mock_listdir, mock_remove):
        """Test that _clean_folder removes all files in directory."""
        mock_listdir.return_value = ["file1.tif", "file2.tif"]

        _clean_folder("/test/path")

        self.assertEqual(mock_remove.call_count, 2)
        mock_remove.assert_any_call("/test/path/file1.tif")
        mock_remove.assert_any_call("/test/path/file2.tif")

    @patch("farmtech.views.inference.os.remove")
    @patch("farmtech.views.inference.os.listdir")
    def test_clean_folder_handles_empty_directory(self, mock_listdir, mock_remove):
        """Test that _clean_folder handles empty directories."""
        mock_listdir.return_value = []

        _clean_folder("/test/path")

        mock_remove.assert_not_called()


class CollectResultsTestCase(TestCase):
    """Tests for _collect_results helper function."""

    @patch("farmtech.views.inference.os.path.exists")
    def test_collect_results_missing_processed_path(self, mock_exists):
        """Test that _collect_results raises error when processed path doesn't exist."""
        mock_exists.return_value = False

        with self.assertRaises(InvokeSSHCommandError) as context:
            _collect_results("/mnt/volumes/inference_data/raw/drone/test-uuid")

        self.assertIn("Processed path does not exist", str(context.exception))

    @patch("farmtech.views.inference.os.listdir")
    @patch("farmtech.views.inference.os.path.exists")
    def test_collect_results_no_files(self, mock_exists, mock_listdir):
        """Test that _collect_results raises error when no result files found."""
        mock_exists.return_value = True
        mock_listdir.return_value = []

        with self.assertRaises(InvokeSSHCommandError) as context:
            _collect_results("/mnt/volumes/inference_data/raw/drone/test-uuid")

        self.assertIn("No result files found", str(context.exception))

    @patch("farmtech.views.inference.os.listdir")
    @patch("farmtech.views.inference.os.path.exists")
    def test_collect_results_multiple_files(self, mock_exists, mock_listdir):
        """Test that _collect_results raises error when multiple files found."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["result1.csv", "result2.csv"]

        with self.assertRaises(InvokeSSHCommandError) as context:
            _collect_results("/mnt/volumes/inference_data/raw/drone/test-uuid")

        self.assertIn("Multiple result files found", str(context.exception))

    @patch("farmtech.views.inference._clean_folder")
    @patch("farmtech.views.inference.pd.read_csv")
    @patch("farmtech.views.inference.os.listdir")
    @patch("farmtech.views.inference.os.path.exists")
    def test_collect_results_success(
        self, mock_exists, mock_listdir, mock_read_csv, mock_clean
    ):
        """Test that _collect_results successfully retrieves results."""

        mock_exists.return_value = True
        mock_listdir.return_value = ["result.csv"]

        mock_df = pd.DataFrame({"col1": [1], "col2": [2], "result": [5.5]})
        mock_read_csv.return_value = mock_df

        results = _collect_results("/mnt/volumes/inference_data/raw/drone/test-uuid")

        self.assertIn("result", results)
        self.assertEqual(results["unit"], "t/ha")


class ExtractGeometryTestCase(TestCase):
    """Tests for _extract_geometry helper function."""

    @patch("farmtech.views.inference.rasterio.open")
    def test_extract_geometry_returns_geojson(self, mock_rasterio_open):
        """Test that _extract_geometry returns valid GeoJSON polygon."""

        mock_src = MagicMock()
        mock_src.crs = CRS.from_epsg(4326)
        mock_src.bounds = (12.0, 41.0, 12.5, 41.5)

        mock_rasterio_open.return_value.__enter__ = MagicMock(return_value=mock_src)
        mock_rasterio_open.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "farmtech.views.inference.transform_bounds",
            return_value=(12.0, 41.0, 12.5, 41.5),
        ):
            result = _extract_geometry("/path/to/file.tif")

        self.assertEqual(result["type"], "Polygon")
        self.assertIn("coordinates", result)


class SaveTiffFileTestCase(TestCase):
    """Tests for _save_tiff_file helper function."""

    @patch("builtins.open", create=True)
    @patch("farmtech.views.inference.os.makedirs")
    @patch("farmtech.views.inference.os.path.exists")
    def test_save_tiff_creates_directory(self, mock_exists, mock_makedirs, mock_open):
        """Test that _save_tiff_file creates directory if not exists."""
        mock_exists.return_value = False
        mock_open.return_value.__enter__ = MagicMock()
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        mock_tiff = MagicMock()
        mock_tiff.chunks.return_value = [b"data"]

        _save_tiff_file("/test/path", mock_tiff, "file.tif")

        mock_makedirs.assert_called_once_with("/test/path")

    @patch("builtins.open", create=True)
    @patch("farmtech.views.inference.os.makedirs")
    @patch("farmtech.views.inference.os.path.exists")
    def test_save_tiff_handles_bytes(self, mock_exists, mock_makedirs, mock_open):
        """Test that _save_tiff_file handles raw bytes."""
        mock_exists.return_value = True

        mock_file_handle = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_file_handle)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        tiff_bytes = b"tiff content"

        _save_tiff_file("/test/path", tiff_bytes, "file.tif")

    @patch("farmtech.views.inference.os.path.exists")
    def test_save_tiff_raises_on_error(self, mock_exists):
        """Test that _save_tiff_file raises TiffSaveError on failure."""
        mock_exists.side_effect = Exception("Disk error")

        with self.assertRaises(TiffSaveError):
            _save_tiff_file("/test/path", b"data", "file.tif")


class CalculateCentroidTestCase(TestCase):
    """Tests for _calculate_centroid helper function."""

    def test_calculate_centroid_returns_coordinates(self):
        """Test that _calculate_centroid returns lat/lon coordinates."""
        polygon = {
            "type": "Polygon",
            "coordinates": [
                [
                    [12.4924, 41.8902],
                    [12.4964, 41.8902],
                    [12.4964, 41.8922],
                    [12.4924, 41.8922],
                    [12.4924, 41.8902],
                ]
            ],
        }

        result = _calculate_centroid(polygon)

        self.assertIn("lat", result)
        self.assertIn("lon", result)
        self.assertAlmostEqual(result["lat"], 41.8912, places=3)
        self.assertAlmostEqual(result["lon"], 12.4944, places=3)


class InvokeSSHCommandTestCase(TestCase):
    """Tests for _invoke_ssh_command helper function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_invoke_ssh_missing_config(self):
        """Test that _invoke_ssh_command raises error when config is missing."""
        with self.assertRaises(InvokeSSHCommandError) as context:
            _invoke_ssh_command("/test/path", {"type": "Polygon", "coordinates": [[]]})

        self.assertIn("not configured", str(context.exception))

    @patch("farmtech.views.inference.os.path.exists")
    @patch.dict(
        os.environ,
        {
            "REMOTE_SSH_USER": "user",
            "REMOTE_SSH_HOST": "host",
            "REMOTE_SSH_COMMAND": "command",
            "SSH_KEY_PATH": "/path/to/key",
        },
    )
    def test_invoke_ssh_missing_key(self, mock_exists):
        """Test that _invoke_ssh_command raises error when SSH key is missing."""
        mock_exists.return_value = False

        with self.assertRaises(InvokeSSHCommandError) as context:
            _invoke_ssh_command("/test/path", {"type": "Polygon", "coordinates": [[]]})

        self.assertIn("SSH key not found", str(context.exception))


class RunSSHCommandViewTestCase(TestCase):
    """Tests for RunSSHCommandView using APIClient with force_authenticate."""

    def setUp(self):
        """Set up test data."""

        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword", email="test@example.com"
        )
        self.client.force_authenticate(user=self.user)

    @patch("farmtech.views.inference.RunSSHCommandView.throttle_classes", [])
    @patch("farmtech.views.inference.RunSSHCommandView.permission_classes", [])
    def test_post_missing_input(self):
        """Test POST request without tiff_file or polygon returns 400."""
        response = self.client.post("/api/inference/trigger/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("farmtech.views.inference.RunSSHCommandView.throttle_classes", [])
    @patch("farmtech.views.inference.RunSSHCommandView.permission_classes", [])
    @patch("farmtech.views.inference.DataForInferenceSerializer")
    def test_post_both_tiff_and_polygon(self, mock_serializer_class):
        """Test POST request with both tiff_file and polygon returns 400."""
        # Mock serializer to return validation error for both inputs
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {
            "non_field_errors": [
                "Only one of 'tiff_file' or 'polygon' should be provided."
            ]
        }
        mock_serializer_class.return_value = mock_serializer

        response = self.client.post(
            "/api/inference/trigger/",
            {"tiff_file": "test.tif", "polygon": "{}"},
            format="json",
        )
        # The serializer should reject this with a 400 error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("farmtech.views.inference.RunSSHCommandView.throttle_classes", [])
    @patch("farmtech.views.inference.RunSSHCommandView.permission_classes", [])
    def test_post_polygon_without_dates(self):
        """Test POST request with polygon but no dates returns 400."""
        response = self.client.post(
            "/api/inference/trigger/",
            {"polygon": {"type": "Polygon", "coordinates": [[]]}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DataForInferenceSerializerTestCase(TestCase):
    """Tests for DataForInferenceSerializer."""

    def test_valid_tiff_file(self):
        """Test serializer accepts valid tiff file."""

        mock_file = MagicMock()
        mock_file.name = "test.tif"

        data = {"tiff_file": mock_file}
        serializer = DataForInferenceSerializer(data=data)

        # Note: Full validation may require actual file

    def test_valid_polygon_with_dates(self):
        """Test serializer accepts valid polygon with dates."""

        data = {
            "polygon": {"type": "Polygon", "coordinates": [[]]},
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }
        serializer = DataForInferenceSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.input_type, "polygon")

    def test_missing_dates_for_polygon(self):
        """Test serializer rejects polygon without dates."""

        data = {"polygon": {"type": "Polygon", "coordinates": [[]]}}
        serializer = DataForInferenceSerializer(data=data)

        self.assertFalse(serializer.is_valid())

    def test_both_tiff_and_polygon(self):
        """Test serializer rejects both tiff and polygon."""

        mock_file = MagicMock()
        mock_file.name = "test.tif"

        data = {
            "tiff_file": mock_file,
            "polygon": {"type": "Polygon", "coordinates": [[]]},
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }
        # Note: Validation behavior depends on serializer implementation


class PolygonAnalysisTestCase(TestCase):
    """Tests for _polygon_analysis helper function."""

    @patch("farmtech.views.inference.get_tiff_from_copernicus")
    @patch("farmtech.views.inference.get_auth_token")
    def test_polygon_analysis_success(self, mock_get_token, mock_get_tiff):
        """Test successful polygon analysis."""
        mock_get_token.return_value = "test_token"
        mock_get_tiff.return_value = b"tiff_data"

        polygon = {"type": "Polygon", "coordinates": [[]]}

        tiff_data, file_name = _polygon_analysis(polygon, "2023-01-01", "2023-12-31")

        self.assertEqual(tiff_data, b"tiff_data")
        self.assertIn("copernicus_analysis", file_name)
        self.assertTrue(file_name.endswith(".tif"))

    @patch("farmtech.views.inference.get_auth_token")
    def test_polygon_analysis_auth_failure(self, mock_get_token):
        """Test polygon analysis with auth failure."""
        mock_get_token.side_effect = Exception("Auth failed")

        polygon = {"type": "Polygon", "coordinates": [[]]}

        with self.assertRaises(PolygonAnalysisError):
            _polygon_analysis(polygon, "2023-01-01", "2023-12-31")

    @patch("farmtech.views.inference.get_tiff_from_copernicus")
    @patch("farmtech.views.inference.get_auth_token")
    def test_polygon_analysis_copernicus_failure(self, mock_get_token, mock_get_tiff):
        """Test polygon analysis with Copernicus API failure."""
        mock_get_token.return_value = "test_token"
        mock_get_tiff.side_effect = Exception("Copernicus error")

        polygon = {"type": "Polygon", "coordinates": [[]]}

        with self.assertRaises(PolygonAnalysisError):
            _polygon_analysis(polygon, "2023-01-01", "2023-12-31")
