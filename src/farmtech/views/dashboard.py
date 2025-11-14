from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from farmtech.authentication import KeycloakAuthentication
from rest_framework.authentication import SessionAuthentication
from geonode.geoapps.models import GeoApp
from farmtech.permissions import IsGroupProfileManager

class PublishDashboardAPIView(APIView):
    """
    API view to update the is_published field to True for a specific post.
    Expected method: PATCH
    URL: /api/dashboard/{pk}/publish/
    
    Requires the user to be a manager of the GroupProfile associated with the dashboard's group.
    """

    authentication_classes = [SessionAuthentication, KeycloakAuthentication]
    permission_classes = [IsAuthenticated, IsGroupProfileManager]

    def patch(self, request, pk):
        dashboard = get_object_or_404(GeoApp, pk=pk)
        
        # Verifica i permessi a livello di oggetto
        self.check_object_permissions(request, dashboard)
        
        if not dashboard.is_approved:
            dashboard.is_published = True
            dashboard.is_approved = True
            dashboard.advertised = True
            dashboard.save(update_fields=['is_published','is_approved','advertised'])

            group = dashboard.group

            group_dashaboard = GeoApp.objects.filter(group=group).exclude(id=dashboard.id).all()
            for geoapp in group_dashaboard:
                if geoapp.id != dashboard.id:
                    geoapp.is_published = False
                    dashboard.is_approved = False
                    geoapp.save(update_fields=['is_published','is_approved'])
            
            return Response({'detail': 'Dashboard successfully published.', 'is_published': True}, status=status.HTTP_200_OK)
        
        return Response({'detail': 'Dashboard is already published.', 'is_published': True}, status=status.HTTP_200_OK)
