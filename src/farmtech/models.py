"""
Farmtech Models
"""

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db import models as gis_models
from geonode.layers.models import Dataset
from geonode.groups.models import GroupProfile


class FarmtechPermissions(models.Model):
    """
    Provides custom permissions for Farmtech app.
    """

    class Meta:
        """
        Meta class for FarmtechPermissions model.
        """

        managed = False
        default_permissions = ()
        permissions = [
            ("uploader", "Can manage research area data"),
            ("viewer", "Can view research area data"),
            ("inference", "Can request area inference"),
            ("can_request_permissions", "Can request uploader or admin permissions"),
        ]


# Raw File model
class RawFile(models.Model):
    """
    Model for raw files.
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
    upload_datetime = models.DateTimeField(
        auto_now_add=True, db_column="upload_datetime"
    )
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, db_column="user"
    )
    dataset_experiment = models.ForeignKey(
        "DatasetExperiment", on_delete=models.RESTRICT, db_column="dataset_experiment"
    )

    class Meta:
        """
        Meta class for RawFile model.
        """

        db_table = "raw_files"
        verbose_name = "Raw File"
        verbose_name_plural = "Raw Files"

    def __str__(self):
        return f"{self.name}"


# Dataset Experiment model (link table between Dataset and GroupProfile)
class DatasetExperiment(models.Model):
    """
    Model for collecting raw datasets to experiments.
    A customized many-to-many association table.

    The model_package field must be in the format: 'app_label.ModelName'
    Example: 'farmtech.Experiment4'
    """

    id = models.AutoField(primary_key=True)
    model_package = models.CharField(
        max_length=255, blank=True, null=True, db_column="model_package"
    )
    template_path = models.CharField(
        max_length=255, blank=True, null=True, db_column="template_path"
    )
    layer_dataset = models.ForeignKey(
        Dataset, on_delete=models.RESTRICT, db_column="layer_dataset"
    )
    group_profile = models.ForeignKey(
        GroupProfile, on_delete=models.RESTRICT, db_column="group_profile"
    )

    class Meta:
        """
        Meta class for DatasetExperiment model.
        """

        db_table = "dataset_experiments"
        verbose_name = "Dataset Experiment"
        verbose_name_plural = "Dataset Experiments"
        unique_together = ["layer_dataset", "group_profile"]

    def __str__(self):
        return f"Dataset {self.layer_dataset.name} - Group_Profile {self.group_profile.title}"


class RoleChangeRequest(models.Model):
    """
    Model for tracking user role change requests.
    Used to limit to 3 requests per day per user.
    """

    MANAGER = "manager"
    MEMBER = "member"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user"
    )
    group_profile = models.ForeignKey(
        GroupProfile, on_delete=models.CASCADE, db_column="group_profile"
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
        """
        Meta class for RoleChangeRequest model.
        """

        db_table = "role_change_requests"
        verbose_name = "Role Change Request"
        verbose_name_plural = "Role Change Requests"
        ordering = ["-request_date"]

    def __str__(self):
        return f"{self.user.username} - {self.request_date.strftime('%Y-%m-%d %H:%M')}"


class Experiment1Sheet1(gis_models.Model):
    """
    Model for the first sheet of Experiment 1.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    year = models.IntegerField(null=True, blank=True, name="year")
    treatment = models.CharField(
        max_length=200, null=True, blank=True, name="treatment"
    )
    gy_barley = models.FloatField(null=True, blank=True, name="gy_barley")
    sy_barley = models.FloatField(null=True, blank=True, name="sy_barley")
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiment1Sheet1 model.
        """

        db_table = "1st_crops"
        managed = False
        verbose_name = "1st_crops"
        verbose_name_plural = "1st_crops"


class Experiment1Sheet2(gis_models.Model):
    """
    Model for the second sheet of Experiment 1.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    year = models.IntegerField(null=True, blank=True, name="year")
    cover_crop_systems = models.CharField(
        max_length=200, null=True, blank=True, name="cover_crop_systems"
    )
    biomass_cover_crop = models.FloatField(
        null=True, blank=True, name="biomass_cover_crop_t_per_ha"
    )
    n_uptake = models.FloatField(null=True, blank=True, name="n_uptake_kg_per_ha")
    p_uptake = models.FloatField(null=True, blank=True, name="p_uptake_kg_per_ha")
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiment1Sheet2 model.
        """

        db_table = "1st_crops_as_cover_crop"
        managed = False
        verbose_name = "1st_crops_as_cover_crop"
        verbose_name_plural = "1st_crops_as_cover_crop"


class Experiment1Sheet3(gis_models.Model):
    """
    Model for the third sheet of Experiment 1.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    year = models.IntegerField(null=True, blank=True, name="year")
    cover_crop_species = models.CharField(
        max_length=200, null=True, blank=True, name="cover_crop_species"
    )
    type_cover_termination = models.CharField(
        max_length=200, null=True, blank=True, name="type_of_cover_termination"
    )
    tomato_yield = models.FloatField(
        null=True, blank=True, name="tomato_yield_kg_per_plant"
    )
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiment1Sheet3 model.
        """

        db_table = "2nd_crops_pomodoro"
        managed = False
        verbose_name = "2nd_crops_pomodoro"
        verbose_name_plural = "2nd_crops_pomodoro"


class Experiemnt1Sheet4(gis_models.Model):
    """
    Model for the fourth sheet of Experiment 1.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    cultivation = models.CharField(
        max_length=200, null=True, blank=True, name="cultivation"
    )
    biomass = models.CharField(max_length=200, null=True, blank=True, name="biomass")
    n_no3 = models.FloatField(null=True, blank=True, name="n-no3_mg_per_kg_soil")
    n_nh4 = models.FloatField(null=True, blank=True, name="n-nh4_mg_per_kg_soil")
    p_olsen = models.FloatField(null=True, blank=True, name="p_olsen_mg_per_kg_soil")
    date = models.DateField(null=True, blank=True, name="date")
    phase = models.IntegerField(null=True, blank=True, name="phase")
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiemnt1Sheet4 model.
        """

        db_table = "azoto_e_fosforo_soil"
        managed = False
        verbose_name = "azoto_e_fosforo_soil"
        verbose_name_plural = "azoto_e_fosforo_soil"


class Experiment3(gis_models.Model):
    """
    Model for Experiment 3.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    tesi = models.CharField(max_length=50, blank=False, null=False, name="tesi")
    data = models.DateField(blank=False, null=False, db_column="data")
    ph = models.FloatField(null=True, blank=True, name="ph")
    ce = models.FloatField(null=True, blank=True, name="ce")
    corg = models.FloatField(null=True, blank=True, name="corg")
    ntot = models.FloatField(null=True, blank=True, name="ntot")
    mbc = models.FloatField(null=True, blank=True, name="mbc")
    mbn = models.FloatField(null=True, blank=True, name="mbn")
    mbc_mbn = models.FloatField(null=True, blank=True, name="mbc_per_mbn")
    rbas = models.FloatField(null=True, blank=True, name="rbas")
    qmin = models.FloatField(null=True, blank=True, name="qmin")
    qco2 = models.FloatField(null=True, blank=True, name="qco2")
    qco2_corg = models.FloatField(null=True, blank=True, name="qco2_per_corg")
    mbc_corg = models.FloatField(null=True, blank=True, name="mbc_per_corg")
    poxc = models.FloatField(null=True, blank=True, name="poxc")
    pma_acida = models.FloatField(null=True, blank=True, name="pma_acida")
    pma_alcalina = models.FloatField(null=True, blank=True, name="pma_alcalina")
    fda = models.FloatField(null=True, blank=True, name="fda")
    ars = models.FloatField(null=True, blank=True, name="ars")
    b_glu = models.FloatField(null=True, blank=True, name="b_glu")
    urease = models.FloatField(null=True, blank=True, name="urease")
    bfi = models.FloatField(null=True, blank=True, name="bfi")
    bfi_star = models.FloatField(null=True, blank=True, name="bfi_star")
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiment3 model.
        """

        db_table = "dati_azione_3"
        managed = False
        verbose_name = "Dati Azione 3"
        verbose_name_plural = "Dati Azione 3"


class Experiment4(gis_models.Model):
    """
    Model for Experiment 4.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    genotipo = models.CharField(max_length=200, null=True, blank=True, name="genotipo")
    trattamento = models.CharField(
        max_length=200, null=True, blank=True, name="trattamento"
    )
    replica = models.IntegerField(null=True, blank=True, name="replica")
    produzione_kg_pianta = models.FloatField(
        null=True, blank=True, name="produzione_kg_per_pianta"
    )
    biomassa_g_pianta = models.FloatField(
        null=True, blank=True, name="biomassa_g_per_pianta"
    )
    spad = models.FloatField(null=True, blank=True, name="spad")
    n_balance_index = models.FloatField(null=True, blank=True, name="n_balance_index")
    n_content_pianta = models.FloatField(null=True, blank=True, name="n_content_pianta")
    nitrato_riduttasi_nr = models.FloatField(
        null=True, blank=True, name="nitrato_riduttasi_nr"
    )
    glutammina_sintetasi_gs = models.FloatField(
        null=True, blank=True, name="glutammina_sintetasi_gs"
    )
    glutammato_gogat = models.FloatField(null=True, blank=True, name="glutammato_gogat")
    nrt2_1 = models.FloatField(null=True, blank=True, name="nrt2.1")
    nrt2_3 = models.FloatField(null=True, blank=True, name="nrt2.3")
    nrt2_4 = models.FloatField(null=True, blank=True, name="nrt2.4")
    nrt3_1 = models.FloatField(null=True, blank=True, name="nrt3.1")
    nr = models.FloatField(null=True, blank=True, name="nr")
    gs = models.FloatField(null=True, blank=True, name="gs")
    gogat = models.FloatField(null=True, blank=True, name="gogat")
    clca = models.FloatField(null=True, blank=True, name="clca")
    lob37 = models.FloatField(null=True, blank=True, name="lob37")
    nrt1_7 = models.FloatField(null=True, blank=True, name="nrt1.7")
    nrt2_7 = models.FloatField(null=True, blank=True, name="nrt2.7")
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiment4 model.
        """

        db_table = "dati_azione_4"
        managed = False
        verbose_name = "Dati Azione 4"
        verbose_name_plural = "Dati Azione 4"


class Experiment5(gis_models.Model):
    """
    Model for Experiment 5.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    sample_id = models.CharField(
        max_length=200, null=True, blank=True, name="sample_id"
    )
    fusarium_fungi_potential_pathogen = models.FloatField(
        null=True, blank=True, name="fusarium_fungi_potential_pathogen"
    )
    alternaria_fungi_potential_pathogen = models.FloatField(
        null=True, blank=True, name="alternaria_fungi_potential_pathogen"
    )
    rhizoctonia_fungi_pathogen = models.FloatField(
        null=True, blank=True, name="rhizoctonia_fungi_pathogen"
    )
    colletotrichum_fungi_pathogen = models.FloatField(
        null=True, blank=True, name="colletotrichum_fungi_pathogen"
    )
    botrytis_fungi_pathogen = models.FloatField(
        null=True, blank=True, name="botrytis_fungi_pathogen"
    )
    xanthomonas_bacteria_potential_pathogen = models.FloatField(
        null=True, blank=True, name="xanthomonas_bacteria_potential_pathogen"
    )
    ralstonia_bacteria_pathogen = models.FloatField(
        null=True, blank=True, name="ralstonia_bacteria_pathogen"
    )
    data_campionamento = models.DateField(
        null=True, blank=True, name="data_campionamento"
    )
    soil = models.CharField(max_length=255, null=True, blank=True, name="soil")
    cover_crop = models.CharField(
        max_length=255, null=True, blank=True, name="cover_crop"
    )
    termination = models.CharField(
        max_length=255, null=True, blank=True, name="termination"
    )
    long = models.FloatField(null=True, blank=True, name="long")
    lat = models.FloatField(null=True, blank=True, name="lat")
    kingdom = models.CharField(max_length=255, null=True, blank=True, name="kingdom")
    observed_richness_number_of_taxa = models.IntegerField(
        null=True, blank=True, name="observed_richness_number_of_taxa"
    )
    diversity_shannon = models.FloatField(
        null=True, blank=True, name="diversity_shannon"
    )
    dominance_simpson = models.FloatField(
        null=True, blank=True, name="dominance_simpson"
    )
    phylogenetic_diversity = models.FloatField(
        null=True, blank=True, name="phylogenetic_diversity"
    )
    fungal_pathogens = models.TextField(null=True, blank=True, name="fungal_pathogens")
    bacterial_pathogens = models.TextField(
        null=True, blank=True, name="bacterial_pathogens"
    )

    class Meta:
        """
        Meta class for Experiment5 model.
        """

        db_table = "dati_azione_5"
        managed = False
        verbose_name = "Dati Azione 5"
        verbose_name_plural = "Dati Azione 5"


class ExperimentZootechnicalCalabria(gis_models.Model):
    """
    Model for Experiment Zootechnical Calabria.
    """

    ogc_fid = models.AutoField(primary_key=True, name="ogc_fid")
    id_campione = models.IntegerField(name="id_campione")
    cereali = models.FloatField(
        null=True, blank=True, name="cereali_loietto_peso_secco_kg_m_2"
    )
    leguminose = models.FloatField(
        null=True,
        blank=True,
        name="leguminose_trifoglio_bianco_peso_secco_kg_m_2",
    )
    altro = models.FloatField(
        null=True,
        blank=True,
        name="altro_crucifere_e_brassicacee_peso_secco_kg_m_2",
    )
    peso_totale = models.FloatField(
        null=True, blank=True, name="peso_totale_peso_secco_kg_m_2"
    )
    ss_105_c = models.FloatField(null=True, blank=True, name="ss_105gradi_c")
    ss_reale = models.FloatField(null=True, blank=True, name="ss_reale")
    ee = models.FloatField(null=True, blank=True, name="ee")
    pg = models.FloatField(null=True, blank=True, name="pg")
    ceneri = models.FloatField(null=True, blank=True, name="ceneri")
    ndf = models.FloatField(null=True, blank=True, name="ndf")
    adf = models.FloatField(null=True, blank=True, name="adf")
    adl = models.FloatField(null=True, blank=True, name="adl")
    periodo = models.FloatField(null=True, blank=True, name="periodo")
    data = models.DateField(null=True, blank=True, name="data")
    inizio_pascolamento = models.DateField(
        null=True, blank=True, name="inizio_pascolamento"
    )
    utilizzazione = models.CharField(
        max_length=255, null=True, blank=True, name="utilizzazione"
    )
    geometry = gis_models.GeometryField(
        srid=4326, null=True, blank=True, name="geometry"
    )

    class Meta:
        """
        Meta class for Experiment Zootechnical Calabria model.
        """

        db_table = "dati_azione_zootecnica_cal"
        managed = False
        verbose_name = "Dati Azione zootecnica Calabria"
        verbose_name_plural = "Dati Azione zootecnica Calabria"


class ExperimentZootechnicalBasilicata(gis_models.Model):
    """
    Model for Experiment Zootechnical Basilicata.
    """

    ogc_fid = models.AutoField(primary_key=True)
    campione = models.CharField(max_length=255, null=True, blank=True, name="campione")
    pascolo = models.CharField(max_length=255, null=True, blank=True, name="pascolo")
    data = models.DateField(null=True, blank=True, name="data")
    prelievo = models.CharField(max_length=255, null=True, blank=True, name="prelievo")
    id_nir = models.CharField(max_length=255, null=True, blank=True, name="id_nir")
    temperatura_suolo_c = models.FloatField(
        null=True, blank=True, name="temperatura_suolo_gradi_c"
    )
    umidita_suolo_percent = models.FloatField(
        null=True, blank=True, name="umidità_suolo_perc"
    )
    altezza_pascolo_cm = models.FloatField(
        null=True, blank=True, name="altezza_pascolo_cm"
    )
    temperatura_aria_c = models.FloatField(
        null=True, blank=True, name="temperatura_aria_gradi_c"
    )
    piogge_mm = models.FloatField(null=True, blank=True, name="piogge_mm")
    biomassa_verde_totale = models.FloatField(
        null=True, blank=True, name="biomassa_verde_totale_g_per_0,25_mq"
    )
    biomassa_verde_pulita = models.FloatField(
        null=True,
        blank=True,
        name="biomassa_verde_pulita_dal_secco_e_messo_in_stufa_g_per_0,25_mq",
    )
    ndvi_media = models.FloatField(null=True, blank=True, name="ndvi_media")
    ndvi_mediana = models.FloatField(null=True, blank=True, name="ndvi_mediana")
    evi_media = models.FloatField(null=True, blank=True, name="evi_media")
    evi_mediana = models.FloatField(null=True, blank=True, name="evi_mediana")
    lai = models.FloatField(null=True, blank=True, name="lai")
    biomassa_secca_totale = models.FloatField(
        null=True, blank=True, name="biomassa_secca_totale_g_per_0,25_mq"
    )
    biomassa_secca_pulita = models.FloatField(
        null=True, blank=True, name="biomassa_secca_pulita_dal_secco_g_per_0,25_mq"
    )
    percent_ss_campione_verde = models.FloatField(
        null=True, blank=True, name="perc_ss_campione_verde"
    )
    percent_ss_campione_pulito = models.FloatField(
        null=True, blank=True, name="perc_ss_campione_pulito"
    )
    peso_graminacee_g = models.FloatField(
        null=True, blank=True, name="peso_graminacee_g"
    )
    peso_leguminose_g = models.FloatField(
        null=True, blank=True, name="peso_leguminose_g"
    )
    peso_composite_g = models.FloatField(null=True, blank=True, name="peso_composite_g")
    peso_altre_g = models.FloatField(null=True, blank=True, name="peso_altre_g")
    percent_graminacee = models.FloatField(
        null=True, blank=True, name="perc_graminacee"
    )
    percent_leguminose = models.FloatField(
        null=True, blank=True, name="perc_leguminose"
    )
    percent_composite = models.FloatField(null=True, blank=True, name="perc_composite")
    percent_altre = models.FloatField(null=True, blank=True, name="perc_altre")
    ss_nir_unibas = models.FloatField(null=True, blank=True, name="ss_nir_unibas")
    ss_ara = models.FloatField(null=True, blank=True, name="ss_ara")
    ndf_ara = models.FloatField(null=True, blank=True, name="ndf_ara")
    ndf_nir_unibas = models.FloatField(null=True, blank=True, name="ndf_nir_unibas")
    ndfunibas = models.FloatField(null=True, blank=True, name="ndfunibas")
    adf_ara = models.FloatField(null=True, blank=True, name="adf_ara")
    adl_ss_ara = models.FloatField(null=True, blank=True, name="adl_ss_ara")
    adf_nir_unibas = models.FloatField(null=True, blank=True, name="adf_nir_unibas")
    adf_unibas = models.FloatField(null=True, blank=True, name="adf_unibas")
    proteine_nir_unibas = models.FloatField(
        null=True, blank=True, name="proteine_nir_unibas"
    )
    prot_insara = models.FloatField(null=True, blank=True, name="prot_insara")
    protsolub_ara = models.FloatField(null=True, blank=True, name="protsolub_ara")
    proteine_ara_kjeldhal = models.FloatField(
        null=True, blank=True, name="protenine_ara_kjeldhal"
    )
    grassi_ss_ara = models.FloatField(null=True, blank=True, name="grassi_ss_ara")
    estratto_etereo_percent_nir_unibas = models.FloatField(
        null=True, blank=True, name="estratto_etereo_perc_nir_unibas"
    )
    fibre_ss_ara = models.FloatField(null=True, blank=True, name="fibre_ss_ara")
    ceneri_ss_ara = models.FloatField(null=True, blank=True, name="ceneri_ss_ara")
    ceneri_percent_nir_unibas = models.FloatField(
        null=True, blank=True, name="ceneri_perc_nir_unibas"
    )
    amido_ss_ara = models.FloatField(null=True, blank=True, name="amido_ss_ara")
    mg_tq_ara = models.FloatField(null=True, blank=True, name="mg_tq_ara")
    s_tq_ara = models.FloatField(null=True, blank=True, name="s_tq_ara")
    ca_ara = models.FloatField(null=True, blank=True, name="ca_ara")
    p_tq_ara = models.FloatField(null=True, blank=True, name="p_tq_ara")
    k_tq_ara = models.FloatField(null=True, blank=True, name="k_tq_ara")
    famiglia_nir = models.CharField(
        max_length=255, null=True, blank=True, name="famiglia_nir"
    )
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True)

    class Meta:
        """
        Meta class for Experiment Zootechnical Basilicata model.
        """

        db_table = "dati_azione_zootecnica_bas"
        managed = False
        verbose_name = "Dati Azione zootecnica Basilicata"
        verbose_name_plural = "Dati Azione zootecnica Basilicata"
