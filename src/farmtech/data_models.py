# TODO add to models.py after first migration
from django.contrib.gis.db import models as gis_models
from django.db import models

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
    geometry = gis_models.GeometryField(srid=4326, null=True, blank=True)

    class Meta:
        db_table = 'azione_zootecnica_basilicata'
        managed = False
        verbose_name = 'Dati Azione zootecnica Basilicata'
        verbose_name_plural = 'Dati Azione zootecnica Basilicata'
