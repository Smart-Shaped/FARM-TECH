import sys
import logging

from django.dispatch import receiver
from geonode.groups.models import GroupProfile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from geonode.geoapps.models import GeoApp

logger = logging.getLogger("django")

# my_custom_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from geonode.resource.models import ExecutionRequest
from geonode.base.models import Group # To look up Group IDs by name
#from geonode.people.models import Profile # To look up User IDs by name
#from geonode.base.models import ResourceBase # For PermSpecCompact

# Assuming these are available from geonode.security.perms_utils or similar
# For this example, we'll import them from our mock setup, but you'd need
# the real ones from GeoNode in your production code.
from geonode.security.permissions import PermSpecCompact
#from geonode.security.perissions import PermSpecUserCompact, PermSpecGroupCompact
#from geonode.base.models import get_anonymous_user # Use the geonode helper

# --- Helper to get common User/Group objects ---
def get_common_permission_targets():
    """Gets the IDs for 'anonymous' and 'registered-members' groups."""
    try:
        # GeoNode's built-in groups
        anonymous_group = Group.objects.get(name='anonymous')
        registered_group = Group.objects.get(name='registered-members')
        return anonymous_group.id, registered_group.id
    except Group.DoesNotExist:
        # Handle case where the groups might not exist (e.g., in a minimal setup)
        return None, None

#
# @receiver(post_save, sender=GeoApp)
def set_default_permissions_on_publish(sender, instance, created, **kwargs):
    """
    Sets 'view' permission for Anonymous and Registered Members when a GeoApp
    is newly created or published.
    """
    # 1. Check if the GeoApp is published and if it was just created (optional check)
    if not instance.is_published:
        # Skip if the resource is not published
        return
        
    # The anonymous group (id=2) and registered-members group (id=3) 
    # are standard in GeoNode. You must verify these IDs in your instance.
    ANONYMOUS_GROUP_ID = 2
    REGISTERED_MEMBERS_GROUP_ID = 3
    
    # You should use the helper to look up IDs based on names for robustness:
    # try:
    #     ANONYMOUS_GROUP_ID, REGISTERED_MEMBERS_GROUP_ID = get_common_permission_targets()
    # except:
    #     # Handle missing groups gracefully
    #     return

    # 2. Define the desired view permissions payload in the compact format
    # The payload MUST reflect the *entire* permission set you want, 
    # not just the new additions, if you were doing a PUT/PATCH from the API.
    # However, since we are doing a PATCH via ExecutionRequest, we should 
    # only provide the difference (the view permissions).
    
    # The API call you are mimicking is likely a PUT or a PATCH against the 
    # /resource/permissions endpoint, which uses the structure below.
    # We will assume a **PATCH** approach to merge the new permissions.
    
    # Permission to add:
    # - Anonymous Group (ID: 2) -> 'view'
    # - Registered Members Group (ID: 3) -> 'view'
    
    # NOTE: The PUT payload you provided also contains:
    # {"organizations":[{"id":6,"permissions":"view"},{"id":4,"permissions":"view"}],"users":[{"id":1000,"permissions":"manage"},{"id":3,"permissions":"manage"},{"id":1,"permissions":"owner"}]}"
    # This suggests that a full permission set is being sent. For a signal 
    # to be safe, it's better to read existing permissions, then merge.
    
    # 3. Create the initial PermSpecCompact object from the current permissions
    # Since we are in a signal and the resource is saved, we can fetch its 
    # current permissions, but a simpler, safer approach is to define only
    # the **patch** and rely on the ExecutionRequest logic to handle the merge.
    
    perms_patch_data = {
        "groups": {
            str(ANONYMOUS_GROUP_ID): "view",
            str(REGISTERED_MEMBERS_GROUP_ID): "view"
        }
    }

    # 4. Create the PermSpecCompact patch object
    # The `PermSpecCompact` class expects the data to be in the format:
    # {"users": {<id>: <perm>}, "groups": {<id>: <perm>}}
    try:
        # The resource is the GeoApp instance itself
        perms_spec_compact_patch = PermSpecCompact(perms_patch_data, instance)
        logger.error(str(perms_patch_data))
        logger.error(str(perms_patch_data.extended))
    except Exception as e:
        # Log the error if the PermSpecCompact class is not found or fails
        print(f"Failed to create PermSpecCompact: {e}")
        return

    # 5. Create the ExecutionRequest
    # We need a user to execute the request, typically the resource owner
    # or a superuser (for safety, use the owner which is passed as a key)
    
    owner_user = instance.owner # The user who owns the GeoApp
    
    # This is the crucial part that executes the permission change asynchronously
    _exec_request = ExecutionRequest.objects.create(
        user=owner_user,
        func_name="set_permissions",
        geonode_resource=instance,
        action="permissions",
        input_params={
            "uuid": instance.uuid,
            "owner": owner_user.username,
            # The .extended property converts the compact patch into the 
            # full GeoNode verbose permission list format.
            "permissions": perms_spec_compact_patch.extended,
            "created": created,
            # IMPORTANT: For a PATCH-like behavior (merging into existing permissions),
            # you would ideally need a function that reads the *current* permissions,
            # merges the patch, and then passes the *merged* extended payload.
            # However, if the `set_permissions` function behind the ExecutionRequest 
            # handles the merge itself when the payload is a partial set (like this one),
            # then using `perms_spec_compact_patch.extended` as a full overwrite is wrong.
            # **The safest way to force a new permission set is to read the current ones, merge, and then submit the full result.**
            
            # Since you don't have the internal utility to read current perms,
            # we will assume `perms_spec_compact_patch.extended` contains ONLY the view perms,
            # and that the backend ExecutionRequest is smart enough to handle a partial update
            # or that the resource has only default perms at this point.
        },
    )
    print(f"Created ExecutionRequest for GeoApp {instance.title} (UUID: {instance.uuid})")


@receiver(post_save, sender=GeoApp)
def dataset_post_save(sender, instance, created, **kwargs):
    logger.error("🔥 Signal post save")
    if not created and instance.is_published:
        logger.error("Published Dashboard!")
        group = instance.group

        group_dashaboard = GeoApp.objects.filter(group=group).exclude(id=instance.id).all()
        for geoapp in group_dashaboard:
            geoapp.is_published = False
            geoapp.is_approved = False
            geoapp.advertised = False
            geoapp.save(update_fields=['is_published','is_approved','advertised'])

    if created:
        logger.error("🔥 Signal created")
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
