from django.db import models


class Experiment(models.Model):
    
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'experiments'
    
class ProcessingChain(models.Model):
    
    id = models.AutoField(primary_key=True)
    processing_method = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    def __str__(self):
        return self.processing_method
    
    class Meta:
        db_table = 'processing_chains'
    
class RawDataset(models.Model):
    
    STATUS_CHOICES = [
        ("not_processed", "not_processed"),
        ("processing", "processing"),
        ("processed", "processed"),
        ("failed", "failed"),
    ]
    TYPE_CHOICES = [
        ("tiff", "tiff"),
        ("excel", "excel"),
        ("csv", "csv"),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    processing_id = models.ForeignKey(ProcessingChain, on_delete=models.CASCADE, null=True, blank=True)
    upload_date = models.DateTimeField()
    upload_user = models.CharField(max_length=150)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="not_processed")

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'raw_datasets'
    
class ProcessedDataset(models.Model):
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    experiment_id = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'processed_datasets'
    
class RawProcessedLink(models.Model):
    
    id = models.AutoField(primary_key=True)
    raw_dataset_id = models.ForeignKey(RawDataset, on_delete=models.CASCADE)
    processed_dataset_id = models.ForeignKey(ProcessedDataset, on_delete=models.CASCADE)

    def __str__(self):
        return f"Link {self.id}: Raw {self.raw_dataset_id.name} -> Processed {self.processed_dataset_id.name}"
    
    class Meta:
        db_table = 'raw_processed_links'
