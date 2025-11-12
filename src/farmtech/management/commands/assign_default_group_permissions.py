from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group


class Command(BaseCommand):
    help = 'Assign permissions to default GeoNode groups'

    def handle(self, *args, **options):
        try:
            anonymous_group = Group.objects.get(name='anonymous')
            registered_group = Group.objects.get(name='registered-members')
            
            perm_165 = Permission.objects.get(pk=165)
            perm_167 = Permission.objects.get(pk=167)
            perm_516 = Permission.objects.get(pk=516)
            perm_515 = Permission.objects.get(pk=515)
            perm_517 = Permission.objects.get(pk=517)
            
            anonymous_group.permissions.add(perm_165, perm_515)
            self.stdout.write(
                self.style.SUCCESS(f'Added permissions to group: {anonymous_group.name}')
            )
            
            registered_group.permissions.add(perm_165, perm_167, perm_516, perm_517)
            self.stdout.write(
                self.style.SUCCESS(f'Added permissions to group: {registered_group.name}')
            )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully assigned permissions to default groups')
            )
            
        except Group.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'Group not found: {str(e)}')
            )
        except Permission.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'Permission not found: {str(e)}. Make sure custom permissions are created first.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
