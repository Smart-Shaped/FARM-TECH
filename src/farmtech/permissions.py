from rest_framework.permissions import IsAuthenticated


class HasInferencePermission(IsAuthenticated):

    """
    Permission class per farmtech.inference
    """

    def has_permission(self, request, view):

        """
        Check if the user has the 'farmtech.inference' permission.
        """

        return super().has_permission(request, view) and request.user.has_perm('farmtech.inference')
