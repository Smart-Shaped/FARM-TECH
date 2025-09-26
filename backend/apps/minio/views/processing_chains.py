from typing import List
import logging
from apps.core.models import RawDataset, ProcessedDataset, RawProcessedLink


logger = logging.getLogger(__name__)
# TODO - Implement actual processing logic in the functions below, don't save ProcessedDataset objects
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

def process_excel_experiment_7(raw_dataset: RawDataset) -> List[ProcessedDataset]:
    logger.info('process_excel_experiment_7 started for RawDataset ID: %s', raw_dataset.id)
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
            NameError: If the function with the given method name is not found.
        """
        
        self.raw_dataset = raw_dataset
        self.method_name = method_name
        
        try:
            self.func = globals()[method_name]
        except KeyError:
            raise NameError(f"Function '{method_name}' not found")

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
            logger.error('Error occurred while processing RawDataset ID: %s, Error: %s', self.raw_dataset.id, e)
            self.raw_dataset.status = "error"
            self.raw_dataset.save()
            raise e
        
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
            pd.save()
            link = RawProcessedLink(raw_dataset_id=self.raw_dataset.id, processed_dataset_id=pd.id)
            link.save()
            logger.info('Link created between RawDataset ID: %s and ProcessedDataset ID: %s', self.raw_dataset.id, pd.id)
