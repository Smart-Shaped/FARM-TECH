"""
Class for handling inference requests.
"""

import subprocess
import logging
import os
import json
import uuid
import pandas as pd
import rasterio
import shapely
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from shapely.geometry import box
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from farmtech.serializers import DataForInferenceSerializer
from farmtech.permissions import HasInferencePermission
from farmtech.utils.copernicus_api import get_auth_token, get_tiff_from_copernicus
from farmtech.exceptions import InvokeSSHCommandError, PolygonAnalysisError, TiffSaveError


logger = logging.getLogger(__name__)

def _clean_folder(path: str):

    """
    Cleans all files in the specified directory.

    Args:
        path (str): The path to the directory to clean.
    """

    # clean folder
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))

def _collect_results(drone_file_path: str) -> dict:

    """
    Collects results from the processed directory corresponding to the drone file path.
    Args:
        drone_file_path (str): The path to the drone file.
    Returns:
        dict: A dictionary containing the results.
    """

    # check results
    processed_path = drone_file_path.replace("raw/drone", "processed")

    # check if processed path exists
    if not os.path.exists(processed_path):
        raise InvokeSSHCommandError(
            "Processed path does not exist, the processing might have failed.")

    files = os.listdir(processed_path)
    results = {}

    # folder must contain only one result file
    if len(files) == 0:
        raise InvokeSSHCommandError(
            "No result files found in the processed directory."
        )
    elif len(files) > 1:
        raise InvokeSSHCommandError(
            "Multiple result files found. Expected only one result file."
        )

    file = files[0]
    df = pd.read_csv(os.path.join(processed_path, file))

    # check if result df is empty
    df = df.dropna()
    if len(df) == 0:
        raise InvokeSSHCommandError(
                "Result file is empty after removing NaN values."
            )

    # extract values
    values = df.to_numpy().tolist()
    results = {
        "result": values[0][2],
        "unit": "t/ha"
    }

    # clean folder
    _clean_folder(drone_file_path)
    _clean_folder(processed_path)

    if results["result"] is None:
        raise InvokeSSHCommandError(
            "Result value is None. There might be an issue with the processing."
        )

    return results

def _extract_geometry(path: str) -> dict:

    """
    Extracts the polygon from a raster file.

    Args:
        path (str): The path to the raster file.

    Returns:
        dict: A GeoJSON representation of the polygon in EPSG:4326.
    """

    with rasterio.open(path) as src:
        dst_crs = CRS.from_epsg(4326)
        bbox = transform_bounds(src.crs, dst_crs, *src.bounds)
        polygon = box(bbox[0], bbox[1], bbox[2], bbox[3])

    points = list(polygon.exterior.coords)
    geojson = {
        "type": "Polygon",
        "coordinates": [points]
    }

    return geojson

def _polygon_analysis(polygon: dict, start_date: str, end_date: str) -> tuple:

    """
    Analyzes the specified polygon by requesting a TIFF image from Copernicus.
    Args:
        polygon (dict): The polygon geometry for analysis.
        start_date (str): The start date for the analysis period.
        end_date (str): The end date for the analysis period.
    Returns:
        tuple: A tuple containing the TIFF data (bytes) and the generated file name.
    """

    try:
        # get auth token
        token = get_auth_token()

        # get tiff from copernicus
        tiff_data = get_tiff_from_copernicus(
            geometry=polygon,
            token=token,
            start_date=start_date,
            end_date=end_date
        )

        file_name = f"copernicus_analysis_{uuid.uuid4().hex}.tif"

        return tiff_data, file_name

    except Exception as e:
        raise PolygonAnalysisError(f"Error during polygon analysis: {str(e)}") from e

def _save_tiff_file(drone_file_path, tiff_file, file_name: str) -> None:

    """
    Save the TIFF file to the specified directory.
    Args:
        drone_file_path (str): The directory path to save the TIFF file.
        tiff_file: The TIFF file to save.
        file_name: The name to save the file as.
    """

    try:

        if not os.path.exists(drone_file_path):
            os.makedirs(drone_file_path)
            logger.info("Created directory %s", drone_file_path)

        # save file in shared folder
        with open(os.path.join(drone_file_path, file_name), 'wb') as f:
            if hasattr(tiff_file, 'chunks'):
                for chunk in tiff_file.chunks():
                    f.write(chunk)
            else:
                f.write(tiff_file)

    except Exception as e:
        raise TiffSaveError(f"Error saving TIFF file: {str(e)}") from e

    logger.info("Saved file %s in %s", file_name, drone_file_path)

def _calculate_centroid(polygon: dict) -> dict:

    """
    Calculates the centroid of a polygon.
    Args:
        polygon (dict): The polygon geometry.
    Returns:
        dict: A dictionary with 'lat' and 'lon' of the centroid.
    """

    shapely_pol = shapely.from_geojson(json.dumps(polygon))
    centroid = shapely_pol.centroid

    return {"lat": centroid.y, "lon": centroid.x}

def _invoke_ssh_command(drone_file_path: str, polygon: dict) -> dict:

    """
    Invokes a predefined SSH command on a remote server.
    Args:
        drone_file_path (str): The path to the drone file.
        polygon (dict): The polygon geometry.
    Returns:
        dict: A dictionary containing the results from the SSH command execution.
    """

    remote_user = os.environ.get("REMOTE_SSH_USER")
    remote_host = os.environ.get("REMOTE_SSH_HOST")
    remote_command = os.environ.get("REMOTE_SSH_COMMAND")
    ssh_key_path = os.getenv("SSH_KEY_PATH", "/run/secrets/django_ssh_key")
    remote_ssh_debug = os.getenv("REMOTE_SSH_DEBUG", "False").lower() == "true"

    if not all([remote_user, remote_host, remote_command]):
        raise InvokeSSHCommandError(
            "SSH connection details are not configured in environment variables."
        )

    try:
        # Check if the SSH key exists and has correct permissions
        if not os.path.exists(ssh_key_path):
            raise InvokeSSHCommandError(f"SSH key not found at {ssh_key_path}")

        # Create a temporary copy of the key with correct permissions
        temp_key_path = "/tmp/temp_ssh_key"
        with open(ssh_key_path, 'rb') as src_file, open(temp_key_path, 'wb') as dest_file:
            dest_file.write(src_file.read())

        # Set proper permissions for the temporary SSH key
        os.chmod(temp_key_path, 0o600)
        logger.info("Created temporary key with permissions 600 at %s", temp_key_path)

        session_folder = drone_file_path.split("/")[-1]

        ssh_command = [
            "ssh",
            "-i", temp_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            #"-v",  # Add verbose output for debugging
            f"{remote_user}@{remote_host}",
            remote_command, "--session_folder", session_folder
        ]

        logger.debug("Executing SSH command: %s", ' '.join(ssh_command))

        result = subprocess.Popen(
            ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = result.communicate()

        if result.returncode == 0:
            logger.info("SSH command executed successfully.")
            results = _collect_results(drone_file_path)
            response_dict = {
                "result": results.get("result"),
                "unit": results.get("unit"),
                "polygon": polygon,
                "center": _calculate_centroid(polygon)
            }

            if remote_ssh_debug:
                response_dict["stdout"] = stdout.decode()
                response_dict["stderr"] = stderr.decode()

            return response_dict
        else:
            raise InvokeSSHCommandError(
                f"SSH command failed with exit code {result.returncode}. \
                Stderr: {stderr.decode()}"
            )

    except FileNotFoundError as e:
        raise InvokeSSHCommandError(
            "The 'ssh' command was not found. Ensure the SSH client \
            is installed and in the system's PATH." + str(e)
        ) from e
    except Exception as e:
        raise InvokeSSHCommandError(
            "An unexpected error occurred while executing SSH command: " + str(e)
        ) from e

class RunSSHCommandView(APIView):

    """
    API to run a predefined SSH command on a remote server.
    The command details (user, host, command) should be configured securely,
    for example, using environment variables, and not passed directly in the request.
    """

    permission_classes = [HasInferencePermission]

    def post(self, request):

        """
        Handle POST request to execute a predefined SSH command on a remote server.
        Expects either a TIFF file or a polygon with start and end dates in the request data.
        The file is saved to a shared directory specified by the DRONE_FILE_PATH
        environment variable. Then an SSH command is executed on a remote host
        configured via environment variables (REMOTE_SSH_USER, REMOTE_SSH_HOST,
        REMOTE_SSH_COMMAND, SSH_KEY_PATH). After successful execution, results
        are collected from the processed directory and returned in the response.
        Returns:
            Response: On success, returns a JSON response with result and unit.
            On failure, returns an error message with appropriate HTTP status code.
        """

        serializer = DataForInferenceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tiff_file = None
        file_name = None

        try:

            drone_file_path = os.getenv("DRONE_FILE_PATH", "/mnt/volumes/inference_data/raw/drone")

            uuid_str = str(uuid.uuid4())
            drone_file_path = os.path.join(drone_file_path, uuid_str)

            if serializer.input_type == 'tiff':
                tiff_file = serializer.validated_data["tiff_file"]
                file_name = tiff_file.name

            if serializer.input_type == 'polygon':
                polygon = serializer.validated_data["polygon"]
                start_date = serializer.validated_data.get("start_date")
                end_date = serializer.validated_data.get("end_date")
                tiff_file, file_name = _polygon_analysis(polygon, start_date, end_date)

            _save_tiff_file(drone_file_path, tiff_file, file_name)

            if serializer.input_type == 'tiff':
                polygon = _extract_geometry(os.path.join(drone_file_path, file_name))

            response_dict = _invoke_ssh_command(drone_file_path, polygon)

            return Response(response_dict, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error processing inference request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
