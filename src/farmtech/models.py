from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from geonode.layers.models import Dataset
from django.contrib.gis.db import models as gis_models
from geonode.groups.models import GroupProfile


# Modello Raw (File)
class RawFile(models.Model):
    """
    Modello per i file raw.
    """
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("processed", "Processed"),
        ("failed", "Failed"),
    ]
    TYPE_CHOICES = [
        ("tiff", "TIFF"),
        ("excel", "Excel"),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=500)
    upload_datetime = models.DateTimeField(auto_now_add=True, db_column='upload_datetime')
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        db_column='user'
    )
    dataset_experiment = models.ForeignKey(
        'DatasetExperiment',
        on_delete=models.RESTRICT,
        db_column='dataset_experiment'
    )

    class Meta:
        db_table = 'raw_files'
        verbose_name = 'Raw File'
        verbose_name_plural = 'Raw Files'

    def __str__(self):
        return self.name


# Modello Dataset Experiment (tabella di collegamento)
class DatasetExperiment(models.Model):
    """
    Modello per collegare i raw dataset agli esperimenti.
    Tabella di associazione many-to-many personalizzata.
    
    Il campo model_package deve essere nel formato: 'app_label.ModelName'
    Esempio: 'farmtech.Experiment4'
    """
    id = models.AutoField(primary_key=True)
    model_package = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        db_column='model_package',
        help_text="Nome del modello Django nel formato 'app_label.ModelName' (es: 'farmtech.Experiment4')"
    )
    template_path = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        db_column='template_path'
    )
    layer_dataset = models.ForeignKey(
        Dataset,
        on_delete=models.RESTRICT,
        db_column='layer_dataset'
    )
    group_profile = models.ForeignKey(
        GroupProfile,
        on_delete=models.RESTRICT,
        db_column='group_profile'
    )

    class Meta:
        db_table = 'dataset_experiments'
        verbose_name = 'Dataset Experiment'
        verbose_name_plural = 'Dataset Experiments'
        unique_together = ['layer_dataset', 'group_profile']

    def __str__(self):
        return f"Dataset {self.layer_dataset.name} - Group_Profile {self.group_profile.title}"


class RoleChangeRequest(models.Model):
    """
    Modello per tracciare le richieste di cambio ruolo degli utenti.
    Usato per limitare a 3 richieste al giorno per utente.
    """

    MANAGER = "manager"
    MEMBER = "member"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='user'
    )
    group_profile = models.ForeignKey(
        GroupProfile,
        on_delete=models.CASCADE,
        db_column='group_profile'
    )
    group_role = models.CharField(
        max_length=10,
        choices=[
            (MANAGER, "Manager"),
            (MEMBER, "Member"),
        ],
    )
    motivazione = models.TextField()
    request_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'role_change_requests'
        verbose_name = 'Role Change Request'
        verbose_name_plural = 'Role Change Requests'
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.request_date.strftime('%Y-%m-%d %H:%M')}"


class Experiment1Sheet1(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    year = models.IntegerField(null=True, blank=True, name='year')
    treatment = models.CharField(max_length=200, null=True, blank=True, name='treatment')
    gy_barley = models.FloatField(null=True, blank=True, name='gy barley')
    sy_barley = models.FloatField(null=True, blank=True, name='sy barley')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')
    
    class Meta:
        db_table = 'azione_1_foglio_1'
        managed = False
        verbose_name = '1st_crops'
        verbose_name_plural = '1st_crops'
    
class Experiment1Sheet2(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    year = models.IntegerField(null=True, blank=True, name='year')
    cover_crop_systems = models.CharField(max_length=200, null=True, blank=True, name='cover crop systems')
    biomass_cover_crop = models.FloatField(null=True, blank=True, name='biomass cover crop (t/ha)')
    n_uptake = models.FloatField(null=True, blank=True, name='n uptake (kg/ha)')
    p_uptake = models.FloatField(null=True, blank=True, name='p uptake (kg/ha)')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')
    
    class Meta:
        db_table = 'azione_1_foglio_2'
        managed = False
        verbose_name = '1st_crops_as_cover_crop'
        verbose_name_plural = '1st_crops_as_cover_crop'
    
class Experiment1Sheet3(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    year = models.IntegerField(null=True, blank=True, name='year')
    cover_crop_species = models.CharField(max_length=200, null=True, blank=True, name='cover crop species')
    type_cover_termination = models.CharField(max_length=200, null=True, blank=True, name='type of cover termination')
    tomato_yield = models.FloatField(null=True, blank=True, name='tomato yield (kg/plant)')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')
    
    class Meta:
        db_table = 'azione_1_foglio_3'
        managed = False
        verbose_name = '2nd_crops_pomodoro'
        verbose_name_plural = '2nd_crops_pomodoro'
    
class Experiemnt1Sheet4(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    cultivation = models.CharField(max_length=200, null=True, blank=True, name='cultivation')
    biomass = models.CharField(max_length=200, null=True, blank=True, name='biomass')
    n_no3 = models.FloatField(null=True, blank=True, name='n-no3 mg/kg soil')
    n_nh4 = models.FloatField(null=True, blank=True, name='n-nh4 mg/kg soil')
    p_olsen = models.FloatField(null=True, blank=True, name='p olsen mg/kg soil')
    date = models.DateField(null=True, blank=True, name='date')
    phase = models.IntegerField(null=True, blank=True, name='phase')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')
    
    class Meta:
        db_table = 'azione_1_foglio_4'
        managed = False
        verbose_name = 'azoto_e_fosforo_soil'
        verbose_name_plural = 'azoto_e_fosforo_soil'


class Experiment3(gis_models.Model):

    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    tesi = models.CharField(max_length=50, blank=False, null=False, name='tesi')
    data = models.DateField(blank=False, null=False, db_column='data')
    ph = models.FloatField(null=True, blank=True, name='ph')
    ce = models.FloatField(null=True, blank=True, name='ce')
    corg = models.FloatField(null=True, blank=True, name='corg')
    ntot = models.FloatField(null=True, blank=True, name='ntot')
    mbc = models.FloatField(null=True, blank=True, name='mbc')
    mbn = models.FloatField(null=True, blank=True, name='mbn')
    mbc_mbn = models.FloatField(null=True, blank=True, name='mbc/mbn')
    rbas = models.FloatField(null=True, blank=True, name='rbas')
    qmin = models.FloatField(null=True, blank=True, name='qmin')
    qco2 = models.FloatField(null=True, blank=True, name='qco2')
    qco2_corg = models.FloatField(null=True, blank=True, name='qco2/corg')
    mbc_corg = models.FloatField(null=True, blank=True, name='mbc/corg')
    poxc = models.FloatField(null=True, blank=True, name='poxc')
    pma_acida = models.FloatField(null=True, blank=True, name='pma acida')
    pma_alcalina = models.FloatField(null=True, blank=True, name='pma alcalina')
    fda = models.FloatField(null=True, blank=True, name='fda')
    ars = models.FloatField(null=True, blank=True, name='ars')
    b_glu = models.FloatField(null=True, blank=True, name='b_glu')
    urease = models.FloatField(null=True, blank=True, name='urease')
    bfi = models.FloatField(null=True, blank=True, name='bfi')
    bfi_star = models.FloatField(null=True, blank=True, name='bfi*')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')

    def __str__(self):
        return f"Table {self.variable}, data {self.data}"
    
    class Meta:
        db_table = 'dati_azione_3'
        managed = False
        verbose_name = 'Dati Azione 3'
        verbose_name_plural = 'Dati Azione 3'


class Experiment4(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    genotipo = models.CharField(max_length=200, null=True, blank=True, name='genotipo')
    trattamento = models.CharField(max_length=200, null=True, blank=True, name='trattamento')
    replica = models.IntegerField(null=True, blank=True, name='replica')
    produzione_kg_pianta = models.FloatField(null=True, blank=True, name='produzione kg/pianta')
    biomassa_g_pianta = models.FloatField(null=True, blank=True, name='biomassa g/pianta')
    spad = models.FloatField(null=True, blank=True, name='spad')
    n_balance_index = models.FloatField(null=True, blank=True, name='n balance index')
    n_content_pianta = models.FloatField(null=True, blank=True, name='n content pianta')
    nitrato_riduttasi_nr = models.FloatField(null=True, blank=True, name='nitrato riduttasi (nr)')
    glutammina_sintetasi_gs = models.FloatField(null=True, blank=True, name='glutammina sintetasi (gs)')
    glutammato_gogat = models.FloatField(null=True, blank=True, name='glutammato (gogat)')
    nrt2_1 = models.FloatField(null=True, blank=True, name='nrt2.1')
    nrt2_3 = models.FloatField(null=True, blank=True, name='nrt2.3')
    nrt2_4 = models.FloatField(null=True, blank=True, name='nrt2.4')
    nrt3_1 = models.FloatField(null=True, blank=True, name='nrt3.1')
    nr = models.FloatField(null=True, blank=True, name='nr')
    gs = models.FloatField(null=True, blank=True, name='gs')
    gogat = models.FloatField(null=True, blank=True, name='gogat')
    clca = models.FloatField(null=True, blank=True, name='clca')
    lob37 = models.FloatField(null=True, blank=True, name='lob37')
    nrt1_7 = models.FloatField(null=True, blank=True, name='nrt1.7')
    nrt2_7 = models.FloatField(null=True, blank=True, name='nrt2.7')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')

    class Meta:
        db_table = 'azione_4'
        managed = False
        verbose_name = 'Dati Azione 4'
        verbose_name_plural = 'Dati Azione 4'


class Experiment5(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    campione = models.CharField(max_length=200, null=True, blank=True, name='campione')
    shannon = models.FloatField(null=True, blank=True, name='shannon')
    simpson = models.FloatField(null=True, blank=True, name='simpson')
    mntd = models.FloatField(null=True, blank=True, name='mntd')
    fusarium = models.FloatField(null=True, blank=True, name='fusarium')
    rhizoctonia = models.FloatField(null=True, blank=True, name='rhizoctonia')
    phytophtora = models.FloatField(null=True, blank=True, name='phytophtora')
    data_campionamento = models.DateField(null=True, blank=True, name='data_campionamento')
    description = models.CharField(max_length=200, null=True, blank=True, name='description')
    long = models.FloatField(null=True, blank=True, name='long')
    lat = models.FloatField(null=True, blank=True, name='lat')
    
    class Meta:
        db_table = 'azione_5'
        managed = False
        verbose_name = 'Dati Azione 5'
        verbose_name_plural = 'Dati Azione 5'

class ExperimentZootechnicalCalabria(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True, name='ogc_fid')
    id_campione = models.IntegerField(name='id campione')
    cereali = models.FloatField(null=True, blank=True, name='cereali [loietto] (peso secco [kg m_2])')
    leguminose = models.FloatField(null=True, blank=True, name='leguminose [trifoglio bianco] (peso secco [kg m_2])')
    altro = models.FloatField(null=True, blank=True, name='altro [crucifere e brassicacee] (peso secco [kg m_2])')
    peso_totale = models.FloatField(null=True, blank=True, name='peso totale (peso secco [kg m_2])')
    ss_105_c = models.FloatField(null=True, blank=True, name='ss 105°c')
    ss_reale = models.FloatField(null=True, blank=True, name='ss reale')
    ee = models.FloatField(null=True, blank=True, name='ee')
    pg = models.FloatField(null=True, blank=True, name='pg')
    ceneri = models.FloatField(null=True, blank=True, name='ceneri')
    ndf = models.FloatField(null=True, blank=True, name='ndf')
    adf = models.FloatField(null=True, blank=True, name='adf')
    adl = models.FloatField(null=True, blank=True, name='adl')
    periodo = models.FloatField(null=True, blank=True, name='periodo')
    data = models.DateField(null=True, blank=True, name='data')
    inizio_pascolamento = models.DateField(null=True, blank=True, name='inizio pascolamento')
    utilizzazione = models.CharField(max_length=255, null=True, blank=True, name='utilizzazione')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True, name='geometry')
    
    class Meta:
        db_table = 'azione_zootecnica_calabria'
        managed = False
        verbose_name = 'Dati Azione zootecnica Calabria'
        verbose_name_plural = 'Dati Azione zootecnica Calabria'
        
class ExperimentZootechnicalBasilicata(gis_models.Model):
    
    ogc_fid = models.AutoField(primary_key=True)
    campione = models.CharField(max_length=255, null=True, blank=True, name='campione')
    pascolo = models.CharField(max_length=255, null=True, blank=True, name='pascolo')
    data = models.DateField(null=True, blank=True, name='data')
    prelievo = models.CharField(max_length=255, null=True, blank=True, name='prelievo')
    id_nir = models.CharField(max_length=255, null=True, blank=True, name='id nir')
    temperatura_suolo_c = models.FloatField(null=True, blank=True, name='temperatura suolo °c')
    umidita_suolo_percent = models.FloatField(null=True, blank=True, name='umidità suolo %')
    altezza_pascolo_cm = models.FloatField(null=True, blank=True, name='altezza pascolo cm')
    temperatura_aria_c = models.FloatField(null=True, blank=True, name='temperatura aria °c')
    piogge_mm = models.FloatField(null=True, blank=True, name='piogge mm')
    biomassa_verde_totale = models.FloatField(null=True, blank=True, name='biomassa verde totale (g/ 0,25 mq)')
    biomassa_verde_pulita = models.FloatField(null=True, blank=True, name='biomassa verde pulita dal secco e messo in stufa (g/ 0,25 mq)')
    ndvi_media = models.FloatField(null=True, blank=True, name='ndvi media')
    ndvi_mediana = models.FloatField(null=True, blank=True, name='ndvi mediana')
    evi_media = models.FloatField(null=True, blank=True, name='evi media')
    evi_mediana = models.FloatField(null=True, blank=True, name='evi mediana')
    lai = models.FloatField(null=True, blank=True, name='lai')
    biomassa_secca_totale = models.FloatField(null=True, blank=True, name='biomassa secca totale (g/0,25 mq)')
    biomassa_secca_pulita = models.FloatField(null=True, blank=True, name='biomassa secca pulita dal secco (g/ 0,25 mq)')
    percent_ss_campione_verde = models.FloatField(null=True, blank=True, name='% ss campione verde')
    percent_ss_campione_pulito = models.FloatField(null=True, blank=True, name='% ss campione pulito')
    peso_graminacee_g = models.FloatField(null=True, blank=True, name='peso graminacee (g)')
    peso_leguminose_g = models.FloatField(null=True, blank=True, name='peso leguminose (g)')
    peso_composite_g = models.FloatField(null=True, blank=True, name='peso composite (g)')
    peso_altre_g = models.FloatField(null=True, blank=True, name='peso altre (g)')
    percent_graminacee = models.FloatField(null=True, blank=True, name='% graminacee')
    percent_leguminose = models.FloatField(null=True, blank=True, name='% leguminose')
    percent_composite = models.FloatField(null=True, blank=True, name='% composite')
    percent_altre = models.FloatField(null=True, blank=True, name='% altre')
    ss_nir_unibas = models.FloatField(null=True, blank=True, name='ss nir unibas')
    ss_ara = models.FloatField(null=True, blank=True, name='ss ara')
    ndf_ara = models.FloatField(null=True, blank=True, name='ndf ara')
    ndf_nir_unibas = models.FloatField(null=True, blank=True, name='ndf nir unibas')
    ndfunibas = models.FloatField(null=True, blank=True, name='ndfunibas')
    adf_ara = models.FloatField(null=True, blank=True, name='adf ara')
    adl_ss_ara = models.FloatField(null=True, blank=True, name='adl ss ara')
    adf_nir_unibas = models.FloatField(null=True, blank=True, name='adf nir unibas')
    adf_unibas = models.FloatField(null=True, blank=True, name='adf unibas')
    proteine_nir_unibas = models.FloatField(null=True, blank=True, name='proteine nir unibas')
    prot_insara = models.FloatField(null=True, blank=True, name='prot_insara')
    protsolub_ara = models.FloatField(null=True, blank=True, name='protsolub ara')
    proteine_ara_kjeldhal = models.FloatField(null=True, blank=True, name='protenine ara kjeldhal')
    grassi_ss_ara = models.FloatField(null=True, blank=True, name='grassi ss ara')
    estratto_etereo_percent_nir_unibas = models.FloatField(null=True, blank=True, name='estratto etereo % nir unibas')
    fibre_ss_ara = models.FloatField(null=True, blank=True, name='fibre ss ara')
    ceneri_ss_ara = models.FloatField(null=True, blank=True, name='ceneri ss ara')
    ceneri_percent_nir_unibas = models.FloatField(null=True, blank=True, name='ceneri % nir unibas')
    amido_ss_ara = models.FloatField(null=True, blank=True, name='amido ss ara')
    mg_tq_ara = models.FloatField(null=True, blank=True, name='mg tq ara')
    s_tq_ara = models.FloatField(null=True, blank=True, name='s tq ara')
    ca_ara = models.FloatField(null=True, blank=True, name='ca ara')
    p_tq_ara = models.FloatField(null=True, blank=True, name='p tq ara')
    k_tq_ara = models.FloatField(null=True, blank=True, name='k tq ara')
    famiglia_nir = models.CharField(max_length=255, null=True, blank=True, name='famiglia nir')
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True)

    class Meta:
        db_table = 'azione_zootecnica_basilicata'
        managed = False
        verbose_name = 'Dati Azione zootecnica Basilicata'
        verbose_name_plural = 'Dati Azione zootecnica Basilicata'
