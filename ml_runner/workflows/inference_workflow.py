"""
Inference workflow for processing remote sensing data.
"""

import os
import re
import logging
from glob import glob
from typing import Dict, Optional
import rasterio
import pandas as pd
import numpy as np
from metaflow import step, FlowSpec, Config, Parameter


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__file__)

class InferenceWorkflow(FlowSpec):

    """
    Inference workflow for processing remote sensing data.
    """

    inference_config = Config(
        "inference_config", 
        help="Path to the configuration file",
        default="configs/inference_config.yaml",
        parser="yaml.safe_load"
    )
    session_folder = Parameter(
        "session_folder",
        type=str,
        help="Folder to store session data",
        required=True
    )

    def _safe_divide(self, numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:

        """
        Performs element-wise division of two numpy arrays, handling division by zero.
        Args:
            numerator (np.ndarray): The numerator array.
            denominator (np.ndarray): The denominator array.
        Returns:
            np.ndarray: The result of the element-wise division.
        """

        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.true_divide(numerator, denominator)
        result[denominator == 0] = np.nan
        return result

    def _calculate_ndvi(self, bands: Dict[str, np.ndarray]) -> Optional[np.ndarray]:

        """
        Calculates the NDVI from NIR and Red bands.
        Args:
            bands (Dict[str, np.ndarray]): A dictionary containing the NIR and Red bands.
        Returns:
            Optional[np.ndarray]: The NDVI array if both NIR and Red 
            bands are present, None otherwise.
        """

        nir = bands.get("nir")
        red = bands.get("red")
        if nir is not None and red is not None:
            return self._safe_divide(nir - red, nir + red)
        return None

    def _extract_date_from_filename(self, filename: str) -> str:

        """
        Extracts the date from a filename in the format YYYY-MM-DD.
        Args:
            filename (str): The filename to extract the date from.
        Returns:
            str: The extracted date in the format YYYY-MM-DD if found, "unknown_date" otherwise.
        """

        match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
        return match.group(0) if match else "unknown_date"

    @step
    def start(self):

        logger.info("Starting inference workflow...")

        self.paths = self.inference_config["data"]
        self.params_feat = self.inference_config["feature_extraction"]
        self.params_model = self.inference_config["simple_model"]

        self.raw_tiff_path = os.path.join(
            os.path.abspath(self.paths["raw_drone"]),
            self.session_folder)
        self.processed_path = os.path.join(
            os.path.abspath(self.paths["processed"]),
            self.session_folder)

        os.makedirs(self.raw_tiff_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)
        logger.info("Raw TIFF path: %s", self.raw_tiff_path)
        logger.info("Processed TIFF path: %s", self.processed_path)

        self.next(self.list_files)

    @step
    def list_files(self):
        logger.info("Listing files...")

        # ms_files = sorted(glob(os.path.join(paths['raw_drone'], '**/*MS*.tif'), recursive=True))
        self.ms_files = sorted(
            glob(
                os.path.join(self.raw_tiff_path, "*.tif"),
                recursive=True))
        if not self.ms_files:
            logger.warning("No multi-spectral TIF files found in '%s'. Pipeline terminated.",
                           self.raw_tiff_path)
            self.go_next = False
        else:
            self.go_next = True
            logger.info("Found %s images to process.", len(self.ms_files))

        self.next({True: self.loop_images, False: self.end}, condition="go_next")

    @step
    def loop_images(self):

        self.next(self.calculate_ndvi, foreach="ms_files")

    @step
    def calculate_ndvi(self):

        self.ms_path = self.input
        logger.info("Performing inference...")

        self.date_tag = self._extract_date_from_filename(os.path.basename(self.ms_path))
        logger.info("\n--- Processing image: %s (Date: %s) ---", 
                    os.path.basename(self.ms_path),
                    self.date_tag)

        # NDVI Calculation
        with rasterio.open(self.ms_path) as src:
            if src.count == 5:
                bands = {
                    name: src.read(band_idx).astype(np.float32)
                    for band_idx, name in self.params_feat["band_order"].items()
                    if name in ["red", "nir"]
                }

                ndvi_array = self._calculate_ndvi(bands)
                if ndvi_array is None:
                    logger.warning("Red or NIR bands missing. Skipping.")
                else:
                    self.mean_ndvi_for_area = np.nanmean(ndvi_array)
                    logger.info("Mean NDVI calculated for the area: %.4f", self.mean_ndvi_for_area)
            else:
                logger.warning("Image does not have 5 bands. Skipping.")

        self.next(self.inference_step)

    @step
    def inference_step(self):

        if hasattr(self, "mean_ndvi_for_area") and self.mean_ndvi_for_area:

            # Apply yield model estimation
            a = self.params_model["ndvi_coefficient_a"]
            b = self.params_model["ndvi_intercept_b"]
            estimated_yield = a * self.mean_ndvi_for_area + b

            logger.info("FINAL YIELD ESTIMATE: %.2f t/ha", estimated_yield)
            output_filename = f"yield_estimate_{self.date_tag}.csv"
            self.output_path = os.path.join(self.processed_path, output_filename)
            os.makedirs(self.processed_path, exist_ok=True)

            result_df = pd.DataFrame(
                [
                    {
                        "date": self.date_tag,
                        "mean_ndvi": self.mean_ndvi_for_area,
                        "estimated_yield_t_ha": estimated_yield,
                    }
                ]
            )
            result_df.to_csv(self.output_path, index=False)
            logger.info("Result saved in: %s", self.output_path)

        self.next(self.join)

    @step
    def join(self, inputs):

        self.next(self.end)

    @step
    def end(self):

        logger.info("Inference workflow completed.")

if __name__ == "__main__":
    InferenceWorkflow()
