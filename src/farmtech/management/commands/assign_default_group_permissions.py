"""
Command to assign permissions to default GeoNode groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group


class Command(BaseCommand):
    """
    Command to assign permissions to default GeoNode groups
    """

    help = "Assign permissions to default GeoNode groups"

    def handle(self, *args, **options):
        try:
            anonymous_group = Group.objects.get(name="anonymous")
            registered_group = Group.objects.get(name="registered-members")
            azione_1_group = Group.objects.get(name="azione-1")
            azione_2_group = Group.objects.get(name="azione-2")
            azione_3_group = Group.objects.get(name="azione-3")
            azione_4_group = Group.objects.get(name="azione-4")
            azione_5_group = Group.objects.get(name="azione-5")
            azione_6_group = Group.objects.get(name="azione-6")
            azione_zootecnica_group = Group.objects.get(name="azione-zootecnica")

            perm_view_res = Permission.objects.get(codename="view_resourcebase")
            perm_download_res = Permission.objects.get(codename="download_resourcebase")
            perm_add_res = Permission.objects.get(codename="add_resourcebase")
            perm_uploader = Permission.objects.get(codename="uploader")
            perm_viewer = Permission.objects.get(codename="viewer")
            perm_inference = Permission.objects.get(codename="inference")
            perm_request = Permission.objects.get(codename="can_request_permissions")

            anonymous_group.permissions.add(perm_view_res, perm_viewer)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added permissions to group: {anonymous_group.name}"
                )
            )

            registered_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added permissions to group: {registered_group.name}"
                )
            )

            azione_1_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added permissions to group: {azione_1_group.name}")
            )

            azione_2_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added permissions to group: {azione_2_group.name}")
            )

            azione_3_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added permissions to group: {azione_3_group.name}")
            )

            azione_4_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added permissions to group: {azione_4_group.name}")
            )

            azione_5_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added permissions to group: {azione_5_group.name}")
            )

            azione_6_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added permissions to group: {azione_6_group.name}")
            )

            azione_zootecnica_group.permissions.add(
                perm_view_res,
                perm_download_res,
                perm_viewer,
                perm_inference,
                perm_request,
                perm_add_res,
                perm_uploader,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added permissions to group: {azione_zootecnica_group.name}"
                )
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully assigned permissions to default groups"
                )
            )

        except Group.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Group not found: {str(e)}"))
        except Permission.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Permission not found: {str(e)}. Make sure custom permissions are created first."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
