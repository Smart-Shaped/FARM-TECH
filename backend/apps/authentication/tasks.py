from celery import shared_task
from django.contrib.auth import get_user_model
from .services import KeycloakService
import logging

logger = logging.getLogger('keycloak')
User = get_user_model()


@shared_task
def sync_user_from_keycloak(keycloak_id):
    """
    Task per sincronizzare un utente da Keycloak
    """
    try:
        service = KeycloakService()
        user = service.sync_user_from_keycloak(keycloak_id)
        
        if user:
            logger.info(f"Successfully synced user {user.email}")
            return f"Synced user {user.email}"
        else:
            logger.warning(f"Failed to sync user {keycloak_id}")
            return f"Failed to sync user {keycloak_id}"
            
    except Exception as e:
        logger.error(f"Error syncing user {keycloak_id}: {str(e)}")
        raise


@shared_task
def sync_all_users_from_keycloak():
    """
    Task per sincronizzare tutti gli utenti da Keycloak
    """
    try:
        service = KeycloakService()
        
        # Ottieni tutti gli utenti che hanno keycloak_id
        users_with_keycloak = User.objects.filter(
            keycloak_id__isnull=False
        ).values_list('keycloak_id', flat=True)
        
        synced_count = 0
        for keycloak_id in users_with_keycloak:
            try:
                service.sync_user_from_keycloak(str(keycloak_id))
                synced_count += 1
            except Exception as e:
                logger.error(f"Failed to sync user {keycloak_id}: {str(e)}")
        
        logger.info(f"Synced {synced_count} users from Keycloak")
        return f"Synced {synced_count} users"
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {str(e)}")
        raise