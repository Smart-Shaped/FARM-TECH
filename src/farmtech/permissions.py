"""
Custom permissions for FarmTech app.
"""

from rest_framework.permissions import IsAuthenticated
from geonode.groups.models import GroupMember, GroupProfile


class HasInferencePermission(IsAuthenticated):
    """
    Permission class for farmtech.inference
    """

    def has_permission(self, request, view):
        """
        Check if the user has the 'farmtech.inference' permission.
        """

        return super().has_permission(request, view) and request.user.has_perm(
            "farmtech.inference"
        )


class IsGroupProfileManager(IsAuthenticated):
    """
    Permission class to verify that the user is a manager of the GroupProfile
    associated with a GeoApp's group.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a manager of the GroupProfile associated with the dashboard's group.
        obj should be a GeoApp instance.
        """
        if not super().has_permission(request, view):
            return False

        if not obj.group:
            return False

        try:
            group_profile = GroupProfile.objects.get(group=obj.group)
        except GroupProfile.DoesNotExist:
            return False

        is_manager = GroupMember.objects.filter(
            group=group_profile, user=request.user, role="manager"
        ).exists()

        return is_manager


class IsGroupProfileMember(IsAuthenticated):
    """
    Permission class to verify that the user is a member (manager or member) of the GroupProfile.

    Can be used with:
    - DatasetExperiment (uses obj.group_profile)
    - GroupProfile (uses obj directly)
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a member of the GroupProfile.
        obj can be a DatasetExperiment or GroupProfile instance.
        """
        if not super().has_permission(request, view):
            return False

        # Determine the GroupProfile from the object
        group_profile = None

        # If the object is a GroupProfile, use it directly
        if isinstance(obj, GroupProfile):
            group_profile = obj
        # If the object has a group_profile attribute (e.g. DatasetExperiment)
        elif hasattr(obj, "group_profile"):
            group_profile = obj.group_profile

        if not group_profile:
            return False

        # Verify if the user is a member (any role) of this GroupProfile
        is_member = GroupMember.objects.filter(
            group=group_profile, user=request.user
        ).exists()

        return is_member
