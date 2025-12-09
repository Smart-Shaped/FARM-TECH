"""
Custom exceptions for the farmtech application.
"""


class PolygonAnalysisError(Exception):
    """Custom exception for errors during polygon analysis."""

    def __init__(self, message="An error occurred during polygon analysis."):
        self.message = message
        super().__init__(message)


class InvokeSSHCommandError(Exception):
    """Custom exception for errors during SSH command invocation."""

    def __init__(self, message="An error occurred while invoking the SSH command."):
        self.message = message
        super().__init__(message)


class TiffSaveError(Exception):
    """Custom exception for errors while saving TIFF files."""

    def __init__(self, message="An error occurred while saving the TIFF file."):
        self.message = message
        super().__init__(message)


class CopernicusAPIError(Exception):
    """Custom exception for errors related to Copernicus API interactions."""

    def __init__(
        self, message="An error occurred while interacting with the Copernicus API."
    ):
        self.message = message
        super().__init__(message)


class GeoserverUtilsError(Exception):
    """Custom exception for errors related to GeoServer utilities."""

    def __init__(self, message="An error occurred while using GeoServer utilities."):
        self.message = message
        super().__init__(message)
