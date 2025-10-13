from django.db import models


class Experiment(models.Model):
    
    name = models.CharField(max_length=255, primary_key=True)
    contributor = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, null=True)
    type = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

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
    
    TYPE_CHOICES = [
        ("db_table", "db_table"),
        ("geoserver_layer", "geoserver_layer"),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    experiment_id = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
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

class ZootechnicalDataCalabria(models.Model):
    
    id = models.AutoField(primary_key=True)
    id_campione = models.CharField(max_length=100, name='ID campione')
    data = models.DateField(name='Data')
    periodo = models.CharField(max_length=100, name='Periodo')
    cereali = models.FloatField(name='Cereali [loietto] (Peso secco [kg m-2])')
    leguminiose = models.FloatField(name='Leguminose [trifoglio bianco] (Peso secco [kg m-2])', blank=True, null=True)
    altro = models.FloatField(name='Altro [crucifere e brassicacee] (Peso secco [kg m-2])', blank=True, null=True)
    peso_totale = models.FloatField(name='Peso totale (Peso secco [kg m-2])')
    ss_105 = models.FloatField(name='SS 105°C', blank=True, null=True)
    ss_reale = models.FloatField(name='SS REALE', blank=True, null=True)
    ee = models.FloatField(name='EE', blank=True, null=True)
    pg = models.FloatField(name='PG', blank=True, null=True)
    ceneri = models.FloatField(name='CENERI', blank=True, null=True)
    ndf = models.FloatField(name='NDF', blank=True, null=True)
    adf = models.FloatField(name='ADF', blank=True, null=True)
    adl = models.FloatField(name='ADL', blank=True, null=True)
    inizio_pascolamento = models.DateField(name='Inizio pascolamento', blank=True, null=True)
    utilizzazione = models.CharField(max_length=100, name='Utilizzazione', blank=True, null=True)
    
    class Meta:
        db_table = 'zootechnical_data_calabria'
class Experiment3(models.Model):

    id = models.AutoField(primary_key=True)
    tesi = models.CharField(max_length=50)
    date = models.DateField()
    ph = models.FloatField()
    ce = models.FloatField()
    corg = models.FloatField()
    ntot = models.FloatField()
    mbc = models.FloatField()
    mbn = models.FloatField()
    mbc_mbn = models.FloatField()
    rbas = models.FloatField()
    qmin = models.FloatField()
    qco2 = models.FloatField()
    qco2_corg = models.FloatField()
    mbc_corg = models.FloatField()
    poxc = models.FloatField()
    pma_acida = models.FloatField()
    pma_alcalina = models.FloatField()
    fda = models.FloatField()
    ars = models.FloatField()
    b_glu = models.FloatField()
    urease = models.FloatField()

    def __str__(self):
        return f"Table {self.variable}, date {self.date}"
    
    class Meta:
        db_table = 'experiment_3'


class Experiment4(models.Model):

    id = models.AutoField(primary_key=True)
    genotipo = models.CharField(max_length=50)
    trattamento = models.CharField(max_length=50)
    replica = models.IntegerField()
    produzione = models.FloatField()
    biomassa = models.FloatField()
    SPAD = models.FloatField()
    n_balance_index = models.FloatField()
    n_content_pianta = models.FloatField()
    nitrato_riduttasi = models.FloatField()
    glutammina_sintetasi = models.FloatField()
    glutammato = models.FloatField()
    nrt2_1 = models.FloatField()
    nrt2_3 = models.FloatField()
    nrt2_4 = models.FloatField()
    nrt3_1 = models.FloatField()
    nr = models.FloatField()
    gs = models.FloatField()
    gogat = models.FloatField()
    clca = models.FloatField()
    lob37 = models.FloatField()
    nrt1_7 = models.FloatField()
    nrt2_7 = models.FloatField()

    def __str__(self):
        return f"Genotipo {self.genotipo}, trattamento {self.trattamento}, replica {self.replica}"
    
    class Meta:
        db_table = 'experiment_4'

class Experiment5(models.Model):

    id = models.AutoField(primary_key=True)
    sample = models.CharField(max_length=50)
    date = models.DateField()
    flag_patogeno = models.BooleanField()
    description = models.CharField(max_length=255)
    lon = models.DecimalField()
    lat = models.DecimalField()
    fusarium = models.FloatField()
    rhizoctonia = models.FloatField()
    phytophtora = models.FloatField()
    shannon = models.FloatField()
    simpson = models.FloatField()
    mntd = models.FloatField()

    def __str__(self):
        return f"Sample {self.sample}, date {self.date}"
    
    class Meta:
        db_table = 'experiment_5'

		 				 						
