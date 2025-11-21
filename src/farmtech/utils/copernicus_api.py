"""
Utils for Copernicus API
"""

import logging
from typing import Dict, Any
import requests
from django.conf import settings
from django.core.cache import cache

from farmtech.exceptions import CopernicusAPIError


# Configure a logger
logger = logging.getLogger(__name__)

# --- Cache key per il token ---
TOKEN_CACHE_KEY = "copernicus_auth_token"


def get_auth_token() -> str:
    """
    Gets an authentication token from Copernicus.
    Uses Django's cache to avoid repeated requests.
    """
    # 1. Check if the token is already in cache
    token = cache.get(TOKEN_CACHE_KEY)
    if token:
        logger.info("Token retrieved from cache.")
        return token

    # 2. If not in cache, request a new one
    logger.info("Requesting new authentication token from Copernicus.")
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.COPERNICUS_CLIENT_ID,
        "client_secret": settings.COPERNICUS_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(
            settings.COPERNICUS_AUTH_URL, data=payload, headers=headers, timeout=20
        )
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)

        data = response.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)  # Duration in seconds

        if not new_token:
            raise ValueError("API response does not contain an access token.")

        # 3. Save the new token in cache with a timeout
        # (subtract 60 seconds for safety)
        cache.set(TOKEN_CACHE_KEY, new_token, timeout=expires_in - 60)
        logger.info("New authentication token saved in cache.")

        return new_token

    except requests.exceptions.RequestException as e:
        logger.error(
            "Error requesting authentication token from Copernicus: %s", str(e)
        )
        raise  # Reraise the exception to be handled in the view


def get_tiff_from_copernicus(
    geometry: Dict[str, Any], token: str, start_date: str = None, end_date: str = None
) -> bytes:
    """
    Requests a TIFF image from Copernicus based on a geometry.
    Returns the binary data of the image.

    Args:
        geometry: GeoJSON geometry of the polygon
        token: Authentication token
        start_date: Start date in format YYYY-MM-DD (optional)
        end_date: End date in format YYYY-MM-DD (optional)
    """
    # Convert dates to ISO format with UTC timezone
    start_datetime = f"{start_date}T00:00:00Z"
    end_datetime = f"{end_date}T23:59:59Z"

    # For simplicity, use the S2L2A configuration as default
    evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B02", "B03", "B04","B08","B11"],
            output: { bands: 5, sampleType: "AUTO" }
          };
        }
        function evaluatePixel(sample) {
          return [sample.B02, sample.B03, sample.B04, sample.B11, sample.B08];
        }
    """

    request_body = {
        "input": {
            "bounds": {
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                "geometry": geometry,
            },
            "data": [
                {
                    "type": "S2L2A",
                    "dataFilter": {
                        "timeRange": {"from": start_datetime, "to": end_datetime},
                        "mosaickingOrder": "mostRecent",
                        "maxCloudCoverage": 20,
                    },
                    "processing": {"downsampling": "NEAREST", "upsamplign": "BICUBIC"},
                }
            ],
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
        },
        "evalscript": evalscript,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "image/tiff",
        "Authorization": f"Bearer {token}",
    }

    try:
        logger.info("Requesting TIFF image from Copernicus.")
        response = requests.post(
            settings.COPERNICUS_API_URL, json=request_body, headers=headers, timeout=20
        )
        response.raise_for_status()
        logger.info("Tiff image received successfully.")
        return response.content  # Binary data of the image

    except requests.exceptions.HTTPError as e:
        raise CopernicusAPIError(
            f"Error requesting TIFF image from Copernicus: {str(e)}"
        ) from e
