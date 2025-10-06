class MinioDownloadError(Exception):
    """Exception raised for errors in the MinIO file download process."""
    
    def __init__(self, message="Error downloading file from MinIO"):
        self.message = message
        super().__init__(self.message)
        
class InsertError(Exception):
    """Exception raised for errors in inserting records into the database."""
    
    def __init__(self, message="Error inserting record into the database"):
        self.message = message
        super().__init__(self.message)
        
class ProcessingChainError(Exception):
    """Exception raised for errors in the processing chain invocation."""
    
    def __init__(self, message="Error invoking processing chain"):
        self.message = message
        super().__init__(self.message)
