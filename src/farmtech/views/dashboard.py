"""API view to publish a dashboard by updating its is_published field to True."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import get_object_or_404
from geonode.geoapps.models import GeoApp
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from farmtech.permissions import IsGroupProfileManager
from farmtech.authentication import KeycloakAuthentication


class PublishDashboardAPIView(APIView):
    """
    API view to update the is_published field to True for a specific post.
    Expected method: PATCH
    URL: /api/dashboard/{pk}/publish/

    Requires the user to be a manager of the GroupProfile associated with the dashboard's group.
    """

    authentication_classes = [SessionAuthentication, KeycloakAuthentication]
    permission_classes = [IsAuthenticated, IsGroupProfileManager]

    @swagger_auto_schema(
        operation_description="Publish a dashboard by setting is_published,"
        " is_approved, and advertised to True. Unpublishes all other dashboards in the same group.",
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="Dashboard ID (GeoApp primary key)",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Dashboard successfully published or already published",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Success message",
                        ),
                        "is_published": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Published status",
                        ),
                    },
                ),
            ),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(
                description="Permission denied - user must be a manager "
                "of the GroupProfile associated with the dashboard"
            ),
            404: openapi.Response(description="Dashboard not found"),
        },
    )
    def patch(self, request, pk):
        """Publish the dashboard by setting is_published to True."""
        dashboard = get_object_or_404(GeoApp, pk=pk)
        self.check_object_permissions(request, dashboard)

        if not dashboard.is_approved:
            dashboard.is_published = True
            dashboard.is_approved = True
            dashboard.advertised = True
            dashboard.save(update_fields=["is_published", "is_approved", "advertised"])

            group = dashboard.group

            group_dashaboard = (
                GeoApp.objects.filter(group=group).exclude(id=dashboard.id).all()
            )
            for geoapp in group_dashaboard:
                if geoapp.id != dashboard.id:
                    geoapp.is_published = False
                    dashboard.is_approved = False
                    geoapp.save(update_fields=["is_published", "is_approved"])

            return Response(
                {"detail": "Dashboard successfully published.", "is_published": True},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Dashboard is already published.", "is_published": True},
            status=status.HTTP_200_OK,
        )
