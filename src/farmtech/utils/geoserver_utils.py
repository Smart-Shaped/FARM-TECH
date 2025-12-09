"""
Utils for GeoServer
"""

import logging
import time
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

from farmtech.exceptions import GeoserverUtilsError

# Configure a logger for debugging
logger = logging.getLogger(__name__)

# GeoServer configuration (add to settings.py)
GEOSERVER_URL = getattr(settings, "GEOSERVER_URL", "http://geoserver:8080/geoserver")
GEOSERVER_USER = getattr(settings, "GEOSERVER_USER", "admin")
GEOSERVER_PASSWORD = getattr(settings, "GEOSERVER_PASSWORD", "geonode")
GEOSERVER_WORKSPACE = getattr(settings, "GEOSERVER_WORKSPACE", "geonode")


def upload_tiff_to_geoserver(tiff_file_path, coverage_name):
    """
    Upload a TIFF file to GeoServer and return the bounding box.
    """
    try:
        logger.info("Starting upload of TIFF file to GeoServer: %s", tiff_file_path)
        logger.info("Coverage name: %s", coverage_name)

        # 1. Ensure the workspace exists
        _ensure_workspace_exists()

        # 2. Create the coverage store by uploading the TIFF
        store_name = f"{coverage_name}_store"
        store_url = (
            f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/"
            f"{store_name}/file.geotiff"
        )

        logger.info("URL for creating coverage store: %s", store_url)

        with open(tiff_file_path, "rb") as f:
            response = requests.put(
                store_url,
                data=f,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                headers={"Content-Type": "image/tiff"},
                params={"configure": "first", "coverageName": coverage_name},
                timeout=60,
            )

        logger.info("Response status code: %s", response.status_code)
        logger.info(
            "Response content: %s", response.text[:500] if response.text else "empty"
        )

        if response.status_code not in [200, 201]:
            logger.error(
                "Error uploading TIFF file to GeoServer: %s", response.status_code
            )
            logger.error("Response: %s", response.text)
            raise GeoserverUtilsError(
                "Error uploading to GeoServer: \
{response.status_code} - {response.text}"
            )

        logger.info("Tiff uploaded to GeoServer: %s", store_name)

        # 3. Wait a moment for GeoServer to process the file
        time.sleep(2)

        # 4. Verify that the coverage has been created - try different names
        possible_names = [
            coverage_name,
            store_name,
            coverage_name.replace("_", "-"),
        ]

        coverage_data = None
        for name in possible_names:
            coverage_url = (
                f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/"
                f"coveragestores/{store_name}/coverages/{name}.json"
            )

            logger.info("Trying to retrieve coverage with name: %s", name)
            logger.info("URL: %s", coverage_url)

            response = requests.get(
                coverage_url,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                timeout=15,
            )

            logger.info("Coverage info status for %s: %s", name, response.status_code)

            if response.status_code == 200:
                coverage_data = response.json()
                coverage_name = name  # Use the name that worked
                logger.info("Coverage found with name: %s", name)
                break

        if not coverage_data:
            # Try listing the available coverages in the store
            list_url = (
                f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/"
                f"coveragestores/{store_name}/coverages.json"
            )
            logger.info("Listing available coverages: %s", list_url)

            response = requests.get(
                list_url,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                timeout=15,
            )

            logger.info("List coverage status: %s", response.status_code)
            logger.info("List coverage: %s", response.text)

            raise GeoserverUtilsError(
                f"Coverage not found after upload to GeoServer. \
Store: {store_name}"
            )

        logger.info("Coverage data retrieved: %s", coverage_data)

        # Extract the bounding box lat/lon
        lat_lon_bbox = coverage_data.get("coverage", {}).get("latLonBoundingBox", {})

        logger.info("Bounding box extracted: %s", lat_lon_bbox)

        # Calculate the center
        if lat_lon_bbox:
            min_x = lat_lon_bbox.get("minx")
            max_x = lat_lon_bbox.get("maxx")
            min_y = lat_lon_bbox.get("miny")
            max_y = lat_lon_bbox.get("maxy")

            if all([min_x, max_x, min_y, max_y]):
                center = [(min_x + max_x) / 2, (min_y + max_y) / 2]
                logger.info("Center calculated: %s", center)
            else:
                center = None
                logger.warning("Coordinate del bbox incomplete")
        else:
            center = None
            logger.warning("latLonBoundingBox non presente")

        return {
            "success": True,
            "layer_name": f"{GEOSERVER_WORKSPACE}:{coverage_name}",
            "store_name": store_name,
            "bounds": lat_lon_bbox,
            "center": center,
        }

    except Exception as e:
        logger.error("Error in upload_tiff_to_geoserver: %s", str(e))
        logger.exception(e)
        raise


def _ensure_workspace_exists():
    """Check if the workspace exists and create it if not"""
    workspace_url = f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}.json"

    logger.info("Checking if workspace exists: %s", workspace_url)
    logger.info("Credenziali: user=%s", workspace_url)

    try:
        response = requests.get(
            workspace_url,
            auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
            timeout=10,
        )

        logger.info("Status check workspace: %s", response.status_code)

        if response.status_code == 404:
            # Il workspace non esiste, crealo
            logger.info("Workspace %s not found, creating it", GEOSERVER_WORKSPACE)
            create_url = f"{GEOSERVER_URL}/rest/workspaces"
            payload = {"workspace": {"name": GEOSERVER_WORKSPACE}}

            response = requests.post(
                create_url,
                json=payload,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            logger.info("Status create workspace: %s", response.status_code)
            logger.info("Response create: %s", response.text)

            if response.status_code not in [200, 201]:
                raise GeoserverUtilsError(
                    f"Error creating workspace: \
{response.status_code} - {response.text}"
                )

            logger.info("Workspace %s created successfully", GEOSERVER_WORKSPACE)

        elif response.status_code == 200:
            logger.info("Workspace %s already exists", GEOSERVER_WORKSPACE)
        else:
            raise GeoserverUtilsError(
                f"Error checking workspace: \
{response.status_code} - {response.text}"
            )

    except requests.exceptions.RequestException as e:
        logger.error("Error connecting to GeoServer: %s", str(e))
        raise GeoserverUtilsError(
            f"Impossibile connettersi a GeoServer: {str(e)}"
        ) from e


def delete_coverage_from_geoserver(store_name, coverage_name):
    """
    Delete a coverage from GeoServer
    """
    try:
        coverage_url = (
            f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/"
            f"coveragestores/{store_name}/coverages/{coverage_name}?recurse=true"
        )

        response = requests.delete(
            coverage_url,
            auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
            timeout=10,
        )

        if response.status_code in [200, 204]:
            logger.info("Coverage %s deleted from GeoServer", coverage_name)
            return True
        else:
            logger.warning("Error deleting coverage: %s", response.status_code)
            return False

    except Exception as e:
        logger.error("Errore in delete_coverage_from_geoserver: %s", str(e))
        return False
