from typing import List
import logging
import os
import tempfile
import pandas as pd
import numpy as np
import datetime
from apps.core.models import RawDataset, ProcessedDataset, RawProcessedLink, ZootechnicalDataCalabria
from apps.minio.exceptions import MinioDownloadError, InsertError, ProcessingChainError


logger = logging.getLogger(__name__)
BUCKET_NAME = "farmtech"
# TODO - Implement actual processing logic in the functions below, don't save ProcessedDataset objects

def _datetime_to_iso(v) -> str:
    
    """
    Convert various datetime types to ISO 8601 string format.
    Handles numpy.datetime64, pandas.Timestamp, datetime.date, and datetime.datetime.
    If conversion fails, returns the string representation of the value.
    
    Args:
        v: The value to convert, can be of various datetime types.
    
    Returns:
        str: The ISO 8601 string representation of the datetime value.
    """
    
    try:
        if isinstance(v, np.datetime64):
            py_dt = pd.to_datetime(v).to_pydatetime()
        elif isinstance(v, pd.Timestamp):
            py_dt = v.to_pydatetime()
        elif isinstance(v, datetime.date) and not isinstance(v, datetime.datetime):
            py_dt = datetime.datetime.combine(v, datetime.time())
        else:
            py_dt = v
        return py_dt.isoformat()
    except Exception:
        return str(v)

def _series_to_kwargs(series: pd.Series) -> dict:

    """
    Convert a pandas Series to a dictionary of keyword arguments.
    Handles missing values, datetime conversions, numpy scalars, float-to-int conversions, and string stripping.
    
    Args:
        series: The pandas Series to convert.
    
    Returns:
        dict: The converted dictionary of keyword arguments.
    """
    
    kwargs = {}
    for col, v in series.items():
        # handle missing
        if pd.isna(v):
            kwargs[col] = None
            continue

        # numpy / pandas datetime -> ISO string
        if isinstance(v, (pd.Timestamp, datetime.datetime, datetime.date, np.datetime64)):
            kwargs[col] = _datetime_to_iso(v)
            continue

        # numpy scalar -> python scalar
        if isinstance(v, np.generic):
            try:
                v = v.item()
            except Exception:
                pass

        # float that is actually an integer value -> int
        if isinstance(v, float) and v.is_integer():
            kwargs[col] = int(v)
            continue

        # strip strings
        if isinstance(v, str):
            kwargs[col] = v.strip()
            continue

        # fallback: pass as-is (often int, bool)
        kwargs[col] = v

    return kwargs

def _minio_download_to_tempfile(raw_dataset: RawDataset) -> pd.DataFrame:
    
    """
    Downloads a file from MinIO to a temporary file and reads it into a pandas DataFrame.
    
    Args:
        raw_dataset: The RawDataset object to download.
    
    Returns:
        pd.DataFrame: The DataFrame containing the data from the downloaded file.
        
    Raises:
        MinioDownloadError: If there is an error downloading or reading the file.
    """
    
    from minio import Minio
    
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    
    logger.info(f"Connecting to MinIO at {minio_endpoint} with access key {minio_access_key}")

    minio_client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False
    )
    
    object_name = raw_dataset.path + "/" + raw_dataset.name
    temp = tempfile.NamedTemporaryFile()
    
    logger.info(f"Downloading object {object_name} from bucket {BUCKET_NAME} to temporary file {temp.name}")

    try:
        minio_client.fget_object(bucket_name=BUCKET_NAME, object_name=object_name, file_path=temp.name)
        df = pd.read_excel(temp.name, dtype=object)
    except Exception as e:
        raise MinioDownloadError(f"Failed to download or read file from MinIO: {e}")
    finally:
        try:
            logger.info(f"Closing temporary file {temp.name}")
            temp.close()
        except Exception:
            pass
    
    return df

def _insert_dataframe_to_model(df: pd.DataFrame, model_class):
    
    """
    Inserts the contents of a pandas DataFrame into a Django model.
    
    Args:
        df: The DataFrame containing the data to insert.
        model_class: The Django model class to insert into.
    
    Raises:
        InsertError: If there is an error inserting a record into the model.
    """
    
    logger.info("Read dataframe: %s rows, %s columns", len(df), len(df.columns))
    logger.info(f"Writing to model {model_class.__name__}...")
    
    records = []
    for index, row in df.iterrows():
        kwargs = _series_to_kwargs(row)
        record = model_class(**kwargs)
        records.append(record)
    try:
        model_class.objects.bulk_create(records)
    except Exception as e:
        raise InsertError(f"Failed to insert records into model {model_class.__name__}: {e}")
    
    logger.info("Finished writing to model %s", model_class.__name__)

def _process_excel(raw_dataset: RawDataset, model_class) -> List[ProcessedDataset]:
    
    """
    Processes an Excel file from a RawDataset and inserts its contents into a specified Django model.
    
    Args:
        raw_dataset: The RawDataset object containing the Excel file to process.
        model_class: The Django model class to insert the data into.
    
    Returns:
        List[ProcessedDataset]: A list of ProcessedDataset objects representing the processed data.
    """
    
    df = _minio_download_to_tempfile(raw_dataset)

    _insert_dataframe_to_model(df, model_class)
    
    # TODO url should be the entrypoint of the view that read the data from the model
    
    processed_dataset = ProcessedDataset(
        name = raw_dataset.name,
        url = model_class._meta.db_table,
        experiment_id = raw_dataset.processing_id.experiment,
        type = "db_table"
    )

    return [processed_dataset]

def process_excel_experiment_1(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('processing_excel_experiment_1 started for RawDataset ID: %s', raw_dataset.id)
    return []

def process_excel_experiment_3(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('processing_excel_experiment_3 started for RawDataset ID: %s', raw_dataset.id)
    return []

def process_excel_experiment_4(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('processing_excel_experiment_4 started for RawDataset ID: %s', raw_dataset.id)
    return []

def process_csv_experiment_5(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('process_csv_experiment_5 started for RawDataset ID: %s', raw_dataset.id)
    return []

def process_excel_experiment_7_calabria(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('process_excel_experiment_7_calabria started for RawDataset ID: %s', raw_dataset.id)

    model_class = ZootechnicalDataCalabria
    try:
        processed_datasets = _process_excel(raw_dataset, model_class)
    except Exception as e:
        raise ProcessingChainError(f"Error processing Excel for RawDataset ID: {raw_dataset.id}, Error: {e}")

    return processed_datasets

def process_excel_experiment_7_basilicata(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('process_excel_experiment_7_basilicata started for RawDataset ID: %s', raw_dataset.id)
    return []

def process_tiff(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('process_tiff started for RawDataset ID: %s', raw_dataset.id)
    return []

class ProcessingChainInvoker:
    
    """
    This class is responsible for invoking the processing functions based on the method name provided.
    It will also update the status of the raw dataset in the database.
    """

    def __init__(self, raw_dataset: RawDataset, method_name: str):
        
        """
        Initializes the ProcessingChainInvoker with the given raw dataset and method name.

        Args:
            raw_dataset (RawDataset): The raw dataset to be processed.
            method_name (str): The name of the processing function to be invoked.

        Raises:
            ProcessingChainError: If the function with the given method name is not found.
        """
        
        self.raw_dataset = raw_dataset
        self.method_name = method_name
        
        try:
            self.func = globals()[method_name]
        except KeyError:
            raise ProcessingChainError(f"Function '{method_name}' not found")

    def invoke(self):
        
        """
        Invokes the processing function with the given raw dataset as argument.
        
        Sets the status of the raw dataset to "processing" and saves it.
        Logs a message to indicate that the processing has started.
        
        Tries to invoke the processing function with the given raw dataset as argument.
        If an exception occurs, sets the status of the raw dataset to "error" and saves it.
        Logs an error message with the exception details.
        Raises the exception.
        
        Sets the status of the raw dataset to "processed" and saves it.
        Logs a message to indicate that the processing has completed.
        
        Populates the links between the raw dataset and the processed datasets.
        """

        self.raw_dataset.status = "processing"
        self.raw_dataset.save()
        logger.info('Processing started for RawDataset ID: %s', self.raw_dataset.id)
        
        processed_datasets = []
        
        try:
            processed_datasets = self.func(self.raw_dataset)
        except Exception as e:
            self.raw_dataset.status = "error"
            self.raw_dataset.save()
            raise ProcessingChainError(f"Error invoking processing chain: {e}")
        
        self.raw_dataset.status = "processed"
        self.raw_dataset.save()
        logger.info('Processing completed for RawDataset ID: %s', self.raw_dataset.id)

        self.populate_links(processed_datasets)

    def populate_links(self, processed_datasets: List[ProcessedDataset]):
        
        """
        Populates the links between the raw dataset and the processed datasets.

        Args:
            processed_datasets (List[ProcessedDataset]): A list of processed datasets.

        Saves the processed datasets and creates a link between the raw dataset and each processed dataset.
        Logs a message to indicate that the link has been created.
        """
        
        for pd in processed_datasets:
            
            try:
                pd.save()
                link = RawProcessedLink(raw_dataset_id=self.raw_dataset, processed_dataset_id=pd)
                link.save()
                logger.info('Link created between RawDataset ID: %s and ProcessedDataset ID: %s', self.raw_dataset.id, pd.id)
            except Exception as e:
                raise InsertError(f"Failed to create link or save ProcessedDataset: {e}")
