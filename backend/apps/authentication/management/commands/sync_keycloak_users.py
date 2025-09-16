from django.core.management.base import BaseCommand
from apps.authentication.services import KeycloakService
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Sincronizza gli utenti da Keycloak'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='ID specifico dell\'utente da sincronizzare',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sincronizza tutti gli utenti',
        )

    def handle(self, *args, **options):
        service = KeycloakService()
        
        if options['user_id']:
            # Sincronizza utente specifico
            user = service.sync_user_from_keycloak(options['user_id'])
            if user:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully synced user {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to sync user {options["user_id"]}')
                )
                
        elif options['all']:
            # Sincronizza tutti gli utenti
            users_with_keycloak = User.objects.filter(
                keycloak_id__isnull=False
            ).values_list('keycloak_id', flat=True)
            
            synced_count = 0
            for keycloak_id in users_with_keycloak:
                try:
                    service.sync_user_from_keycloak(str(keycloak_id))
                    synced_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to sync {keycloak_id}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Synced {synced_count} users from Keycloak')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --user-id or --all')
            )