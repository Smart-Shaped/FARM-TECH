import os
import re
import logging
import rasterio
import shutil
import pandas as pd
import numpy as np
from glob import glob
from typing import Dict, Optional
from metaflow import step, Config, Parameter
from metaflow.plugins.datatools.s3.s3 import S3Object

from chameleon.ml.metaflow.base_flows.config import ConfigurableFlow
from chameleon.ml.metaflow.decorators.data_sources import data_source


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__file__)


class InferenceWorkflow(ConfigurableFlow):
        
    tiff_key = Parameter("tiff_key", help="Key for the input TIFF file for inference", default=None, type=str, required=True)
    inference_config = Config("inference_config", help="Path to the configuration file", default="configs/inference_config.yaml", parser="yaml.safe_load")
    
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
            Optional[np.ndarray]: The NDVI array if both NIR and Red bands are present, None otherwise.
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
        
        self.query_dict = {
            "bucket": "farmtech",
            }
        tiff_key = self.tiff_key.strip()
        if "," in tiff_key:
            self.query_dict["keys"] = [key.strip() for key in tiff_key.split(",")]
        else:
            self.query_dict["key"] = tiff_key

        self.paths = self.inference_config["data"]
        self.params_feat = self.inference_config["feature_extraction"]
        self.params_model = self.inference_config["simple_model"]
        
        self.raw_tiff_path = os.path.abspath(self.paths["raw_drone"])
        self.processed_tiff_path = os.path.abspath(self.paths["processed"])

        os.makedirs(self.raw_tiff_path, exist_ok=True)
        os.makedirs(self.processed_tiff_path, exist_ok=True)
        logger.info(f"Raw TIFF path: {self.raw_tiff_path}")
        logger.info(f"Processed TIFF path: {self.processed_tiff_path}")
        
        self.next(self.download_data)
        
    @data_source(source_type="minio", conn_id="object_storage")
    @step
    def download_data(self):
        logger.info("Downloading data...")
        
        data = self.object_storage.read(query_dict=self.query_dict)
        
        if type(data) is S3Object:
            data = [data]
        
        for obj in data:
            with open(os.path.join(self.raw_tiff_path, os.path.basename(obj.key)), "wb") as f:
                f.write(obj.blob)
        
        self.next(self.list_files)
        
    @step
    def list_files(self):
        logger.info("Listing files...")

        # ms_files = sorted(glob(os.path.join(paths['raw_drone'], '**/*MS*.tif'), recursive=True))
        self.ms_files = sorted(glob(os.path.join(os.path.abspath(self.paths["raw_drone"]), "*.tif"), recursive=True))
        if not self.ms_files:
            logger.warning(
                f"No multi-spectral TIF files found in '{self.paths['raw_drone']}'. Pipeline terminated."
            )
            self.go_next = False
        else:
            self.go_next = True
            logger.info(f"Found {len(self.ms_files)} images to process.")

        self.next({True: self.loop_images, False: self.end}, condition="go_next")
        
    @step
    def loop_images(self):
        self.next(self.calculate_ndvi, foreach="ms_files")
    
    @step
    def calculate_ndvi(self):
        
        self.ms_path = self.input
        logger.info("Performing inference...")
        
        self.date_tag = self._extract_date_from_filename(os.path.basename(self.ms_path))
        logger.info(
            f"\n--- Processing image: {os.path.basename(self.ms_path)} (Date: {self.date_tag}) ---"
        )
        
        # NDVI Calculation
        with rasterio.open(self.ms_path) as src:
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
                logger.info(
                    f"Mean NDVI calculated for the area: {self.mean_ndvi_for_area:.4f}"
                )
        
        self.next(self.inference_step)

    @step
    def inference_step(self):
        
        if self.mean_ndvi_for_area:
        
            # Apply yield model estimation
            a = self.params_model["ndvi_coefficient_a"]
            b = self.params_model["ndvi_intercept_b"]
            estimated_yield = a * self.mean_ndvi_for_area + b

            logger.info(f"FINAL YIELD ESTIMATE: {estimated_yield:.2f} t/ha")
            output_filename = f"yield_estimate_{self.date_tag}.csv"
            self.output_path = os.path.abspath(os.path.join(self.paths["processed"], output_filename))
            os.makedirs(self.paths["processed"], exist_ok=True)

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
            logger.info(f"Result saved in: {self.output_path}")
        
        self.next(self.join)

    @step
    def join(self, inputs):
        
        self.output_paths = [inp.output_path for inp in inputs if hasattr(inp, 'output_path')]
        self.query_dict = inputs[0].query_dict
        self.processed_tiff_path = inputs[0].processed_tiff_path
        self.raw_tiff_path = inputs[0].raw_tiff_path
        
        self.next(self.save_results)
        
    @data_source(source_type="minio", conn_id="object_storage")
    @step
    def save_results(self):
        
        logger.info("Saving results...")
        
        if len(self.output_paths) == 1:
            raw_minio_path_list = [self.query_dict["key"]]
        else:
            raw_minio_path_list = self.query_dict["keys"]
        key_paths = []
        for i, path in enumerate(self.output_paths):
            key = raw_minio_path_list[i]
            key = key.replace("raw_data/tiff", "forecast")
            key_filename = os.path.basename(key)
            path_filename = os.path.basename(path)
            key = key.replace(key_filename, path_filename)
            key_path = (key, path)
            print(key_path)
            key_paths.append(key_path)
        
        upload_query_dict = {
            "bucket": "farmtech",
            "key_paths": key_paths,
        }
        
        self.object_storage.write(
            data=None,
            query_dict=upload_query_dict,
        )
        
        self.next(self.end)

    @step
    def end(self):
        logger.info("Removing temporary files...")
        
        shutil.rmtree(self.processed_tiff_path, ignore_errors=True)
        shutil.rmtree(self.raw_tiff_path, ignore_errors=True)
        
        logger.info("Inference workflow completed.")
        
if __name__ == "__main__":
    InferenceWorkflow()
