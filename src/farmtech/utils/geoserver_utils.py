import requests
import logging
from django.conf import settings
from requests.auth import HTTPBasicAuth

# Configura un logger per il debug
logger = logging.getLogger(__name__)

# Configurazioni GeoServer (da aggiungere in settings.py)
GEOSERVER_URL = getattr(settings, 'GEOSERVER_URL', 'http://geoserver:8080/geoserver')
GEOSERVER_USER = getattr(settings, 'GEOSERVER_USER', 'admin')
GEOSERVER_PASSWORD = getattr(settings, 'GEOSERVER_PASSWORD', 'geonode')
GEOSERVER_WORKSPACE = getattr(settings, 'GEOSERVER_WORKSPACE', 'geonode')


def upload_tiff_to_geoserver(tiff_file_path, coverage_name):
    """
    Carica un file TIFF su GeoServer e restituisce il bounding box.
    """
    try:
        logger.info(f"Inizio upload TIFF su GeoServer: {tiff_file_path}")
        logger.info(f"Coverage name: {coverage_name}")
        
        # 1. Crea il workspace se non esiste
        _ensure_workspace_exists()
        
        # 2. Crea il coverage store caricando il TIFF
        store_name = f"{coverage_name}_store"
        store_url = (
            f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/"
            f"{store_name}/file.geotiff"
        )
        
        logger.info(f"URL caricamento: {store_url}")
        
        with open(tiff_file_path, 'rb') as f:
            response = requests.put(
                store_url,
                data=f,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                headers={'Content-Type': 'image/tiff'},
                params={'configure': 'first', 'coverageName': coverage_name}
            )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text[:500] if response.text else 'empty'}")
        
        if response.status_code not in [200, 201]:
            logger.error(f"Errore caricamento TIFF su GeoServer")
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Errore caricamento su GeoServer: {response.status_code} - {response.text}")
        
        logger.info(f"TIFF caricato con successo su GeoServer: {store_name}")
        
        # 3. Aspetta un momento che GeoServer elabori
        import time
        time.sleep(2)
        
        # 4. Verifica che il coverage sia stato creato - prova diverse possibili nomenclature
        possible_names = [
            coverage_name,
            store_name,
            coverage_name.replace('_', '-'),
        ]
        
        coverage_data = None
        for name in possible_names:
            coverage_url = (
                f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/"
                f"coveragestores/{store_name}/coverages/{name}.json"
            )
            
            logger.info(f"Provo a recuperare coverage con nome: {name}")
            logger.info(f"URL: {coverage_url}")
            
            response = requests.get(
                coverage_url,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD)
            )
            
            logger.info(f"Coverage info status per {name}: {response.status_code}")
            
            if response.status_code == 200:
                coverage_data = response.json()
                coverage_name = name  # Usa il nome che ha funzionato
                logger.info(f"Coverage trovato con nome: {name}")
                break
        
        if not coverage_data:
            # Proviamo a listare i coverage disponibili nello store
            list_url = (
                f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/"
                f"coveragestores/{store_name}/coverages.json"
            )
            logger.info(f"Listo i coverage disponibili: {list_url}")
            
            response = requests.get(
                list_url,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD)
            )
            
            logger.info(f"Lista coverage status: {response.status_code}")
            logger.info(f"Lista coverage: {response.text}")
            
            raise Exception(f"Coverage non trovato dopo il caricamento. Store: {store_name}")
        
        logger.info(f"Coverage data ricevuto: {coverage_data}")
        
        # Estrai il bounding box lat/lon
        lat_lon_bbox = coverage_data['coverage'].get('latLonBoundingBox', {})
        
        logger.info(f"Bounding box estratto: {lat_lon_bbox}")
        
        # Calcola il centro
        if lat_lon_bbox:
            min_x = lat_lon_bbox.get('minx')
            max_x = lat_lon_bbox.get('maxx')
            min_y = lat_lon_bbox.get('miny')
            max_y = lat_lon_bbox.get('maxy')
            
            if all([min_x, max_x, min_y, max_y]):
                center = [
                    (min_x + max_x) / 2,
                    (min_y + max_y) / 2
                ]
                logger.info(f"Centro calcolato: {center}")
            else:
                center = None
                logger.warning(f"Coordinate del bbox incomplete")
        else:
            center = None
            logger.warning("latLonBoundingBox non presente")
        
        return {
            'success': True,
            'layer_name': f"{GEOSERVER_WORKSPACE}:{coverage_name}",
            'store_name': store_name,
            'bounds': lat_lon_bbox,
            'center': center
        }
        
    except Exception as e:
        logger.error(f"ERRORE COMPLETO in upload_tiff_to_geoserver: {str(e)}")
        logger.exception(e)
        raise


def _ensure_workspace_exists():
    """Crea il workspace se non esiste già"""
    workspace_url = f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}.json"
    
    logger.info(f"Verifico esistenza workspace: {workspace_url}")
    logger.info(f"Credenziali: user={GEOSERVER_USER}")
    
    try:
        response = requests.get(
            workspace_url,
            auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
            timeout=10
        )
        
        logger.info(f"Status verifica workspace: {response.status_code}")
        
        if response.status_code == 404:
            # Il workspace non esiste, crealo
            logger.info(f"Workspace {GEOSERVER_WORKSPACE} non trovato, lo creo")
            create_url = f"{GEOSERVER_URL}/rest/workspaces"
            payload = {
                "workspace": {
                    "name": GEOSERVER_WORKSPACE
                }
            }
            
            response = requests.post(
                create_url,
                json=payload,
                auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            logger.info(f"Status creazione workspace: {response.status_code}")
            logger.info(f"Response creazione: {response.text}")
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Errore creazione workspace: {response.status_code} - {response.text}")
            
            logger.info(f"Workspace {GEOSERVER_WORKSPACE} creato con successo")
            
        elif response.status_code == 200:
            logger.info(f"Workspace {GEOSERVER_WORKSPACE} già esistente")
        else:
            raise Exception(f"Errore verifica workspace: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore di connessione a GeoServer: {str(e)}")
        raise Exception(f"Impossibile connettersi a GeoServer: {str(e)}")


def delete_coverage_from_geoserver(store_name, coverage_name):
    """
    Elimina un coverage da GeoServer
    """
    try:
        coverage_url = (
            f"{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/"
            f"coveragestores/{store_name}/coverages/{coverage_name}?recurse=true"
        )
        
        response = requests.delete(
            coverage_url,
            auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD)
        )
        
        if response.status_code in [200, 204]:
            logger.info(f"Coverage {coverage_name} eliminato da GeoServer")
            return True
        else:
            logger.warning(f"Errore eliminazione coverage: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Errore in delete_coverage_from_geoserver: {e}")
        return False