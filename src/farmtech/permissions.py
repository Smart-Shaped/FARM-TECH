from rest_framework.permissions import IsAuthenticated
from geonode.groups.models import GroupMember, GroupProfile


class HasInferencePermission(IsAuthenticated):

    """
    Permission class per farmtech.inference
    """

    def has_permission(self, request, view):

        """
        Check if the user has the 'farmtech.inference' permission.
        """

        return super().has_permission(request, view) and request.user.has_perm('farmtech.inference')


class IsGroupProfileManager(IsAuthenticated):
    """
    Permission class per verificare che l'utente sia un manager del GroupProfile
    associato al gruppo della dashboard.
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
            group=group_profile,
            user=request.user,
            role='manager'
        ).exists()
        
        return is_manager


class IsGroupProfileMember(IsAuthenticated):
    """
    Permission class per verificare che l'utente sia membro (manager o member) del GroupProfile.
    
    Funziona con:
    - DatasetExperiment (usa obj.group_profile)
    - GroupProfile (usa obj direttamente)
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a member of the GroupProfile.
        obj can be a DatasetExperiment or GroupProfile instance.
        """
        if not super().has_permission(request, view):
            return False
        
        # Determina il GroupProfile dall'oggetto
        group_profile = None
        
        # Se l'oggetto è un GroupProfile, usalo direttamente
        if isinstance(obj, GroupProfile):
            group_profile = obj
        # Se l'oggetto ha un attributo group_profile (es. DatasetExperiment)
        elif hasattr(obj, 'group_profile'):
            group_profile = obj.group_profile
        
        if not group_profile:
            return False
        
        # Verifica se l'utente è membro (qualsiasi ruolo) di questo GroupProfile
        is_member = GroupMember.objects.filter(
            group=group_profile,
            user=request.user
        ).exists()
        
        return is_member
