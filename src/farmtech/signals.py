import sys
import logging

from django.dispatch import receiver
from geonode.groups.models import GroupProfile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from geonode.geoapps.models import GeoApp
from geonode.security.permissions import PermSpec, PermSpecCompact
from geonode.resource.api.tasks import resouce_service_dispatcher

logger = logging.getLogger("django")

@receiver(post_save, sender=GeoApp)
def dataset_post_save(sender, instance, created, **kwargs):
    if not created and instance.is_approved:

        group = instance.group
        user = instance.owner

        new_user_perms = ['view_resourcebase','change_resourcebase',]
        # perms_spec_patch = perms_spec = PermSpec(new_user_perms, instance)
        # perms_spec_compact_patch = PermSpecCompact(perms_spec_patch.compact, instance)
        new_groups_perms = {
             "anonymous": ["view_resourcebase"],
        }
        json_perms = instance.get_all_level_info()
        json_perms["groups"] = new_groups_perms
        json_perms["users"][user.username] = new_user_perms
        perms_spec = PermSpec(json_perms, instance)
        perms_spec_compact = PermSpecCompact(perms_spec.compact, instance)
        # perms_spec_compact.merge(perms_spec_compact_patch)
        
        set_permissions(instance, user, perms_spec_compact)

        group_dashaboard = GeoApp.objects.filter(group=group).exclude(id=instance.id).all()
        for geoapp in group_dashaboard:
            geoapp.is_published = False
            geoapp.is_approved = False
            geoapp.save(update_fields=['is_published','is_approved'])
            new_user_perms = {
                "users": {
                    geoapp.owner.username: ['view_resourcebase',
                                    'change_resourcebase',],
                },
                "groups":{}
            }
            perms_geo_patch = perms_spec = PermSpec(new_user_perms, geoapp)
            perms_geo_compact_patch = PermSpecCompact(perms_geo_patch.compact, geoapp)
            json_perms = instance.get_all_level_info()
            perms_geo = PermSpec(json_perms, geoapp)
            perms_geo_compact = PermSpecCompact(perms_geo.compact, geoapp)
            perms_geo_compact.merge(perms_geo_compact_patch)
            
            set_permissions(geoapp, geoapp.owner, perms_geo_compact)

    if created:
        user = instance.owner
        if not user:
            return

        group_profile = GroupProfile.objects.filter(groupmember__user=user).first()
        if group_profile:
            group = group_profile.group
            instance.group = group
            instance.is_published = False
            instance.is_approved = False
            instance.advertised = False
            instance.save()

def set_permissions(resource, user, perms_spec_compact=PermSpecCompact):
    from geonode.resource.models import ExecutionRequest
    _exec_request = ExecutionRequest.objects.create(
        user=user,
        func_name="set_permissions",
        geonode_resource=resource,
        action="permissions",
        input_params={
            "uuid": resource.uuid,
            "owner": user.username,
            "permissions": perms_spec_compact.extended,
            "created": False,
        },
    )
    resouce_service_dispatcher.apply_async(args=(str(_exec_request.exec_id),), expiration=30)
