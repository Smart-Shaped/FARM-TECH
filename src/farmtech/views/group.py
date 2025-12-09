"""
FarmTech Views - Group Profile APIs
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from geonode.geoapps.models import GeoApp
from geonode.groups.models import GroupProfile, GroupMember
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from farmtech.models import RoleChangeRequest
from farmtech.authentication import KeycloakAuthentication
from farmtech.throttles import FivePerDay
from farmtech.serializers import GroupJoinRequestSerializer


logger = logging.getLogger(__name__)

_TEMPLATE_VIEW = "/usr/src/farmtech/resources/group_join_request_email.txt"


class GroupJoinRequestAPIView(APIView):
    """
    API to request membership in a Group Profile.

    Sends an email to all the managers of the requested Group Profile with the information
    of the user, the requested role and the motivation of the request.

    Required parameters:
    - group_profile_id: ID of the Group Profile to join
    - requested_role: Requested role ('manager' or 'member')
    - motivation: Motivation of the request (can be a long text)

    The user who makes the request is automatically retrieved from the authentication token.
    """

    authentication_classes = [KeycloakAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [FivePerDay]

    @swagger_auto_schema(
        operation_description="Request membership in a Group Profile. Sends an email to all group managers with user information, requested role, and motivation.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["group_profile_id", "requested_role", "motivation"],
            properties={
                "group_profile_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the Group Profile to join",
                ),
                "requested_role": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Requested role in the group",
                    enum=["manager", "member"],
                ),
                "motivation": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Motivation for joining the group",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Membership request sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "details": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "group_profile": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "requested_role": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "managers_notified": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                "request_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid data or user already a member with requested role"
            ),
            401: openapi.Response(description="Authentication required"),
            404: openapi.Response(description="GroupProfile not found"),
            429: openapi.Response(description="Rate limit exceeded"),
            500: openapi.Response(
                description="No managers found, email template error, or internal server error"
            ),
        },
    )
    def post(self, request):
        """
        Handle POST request to send a group join request.
        """
        serializer = GroupJoinRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group_profile_id = serializer.validated_data["group_profile_id"]
        requested_role = serializer.validated_data["requested_role"]
        motivation = serializer.validated_data["motivation"]
        user = request.user

        try:
            try:
                group_profile = GroupProfile.objects.get(id=group_profile_id)
            except GroupProfile.DoesNotExist:
                logger.error(
                    "GroupProfile with ID %s not found for join request by user %s",
                    group_profile_id,
                    user.username,
                )
                return Response(
                    {"error": f"GroupProfile with ID {group_profile_id} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            existing_membership = GroupMember.objects.filter(
                group=group_profile, user=user, role=requested_role
            ).first()

            if existing_membership:
                return Response(
                    {
                        "error": "You are already a member of this group with the requested role.",
                        "current_role": existing_membership.role,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            managers = GroupMember.objects.filter(
                group=group_profile, role="manager"
            ).select_related("user")

            if not managers.exists():
                logger.warning(
                    "No managers found for GroupProfile %s (ID: %s)",
                    group_profile.title,
                    group_profile_id,
                )
                return Response(
                    {
                        "error": "No managers found for this group."
                        " Please contact the system administrator."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            role_label = "Manager" if requested_role == "manager" else "Member"
            subject = f"New membership request for group '{group_profile.title}'"

            try:
                with open(_TEMPLATE_VIEW, "r", encoding="utf-8") as f:
                    message_template = f.read()
            except FileNotFoundError:
                logger.exception(
                    "Email template not found: %s", _TEMPLATE_VIEW, exc_info=True
                )
                return Response(
                    {"error": "Internal error: email template not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            message = message_template.format(
                user_full_name=user.get_full_name() or "Not specified",
                user_email=user.email,
                group_title=group_profile.title,
                username=user.username,
                role_label=role_label,
                motivation=motivation,
            )

            manager_emails = [
                manager.user.email for manager in managers if manager.user.email
            ]

            if not manager_emails:
                logger.warning(
                    "No managers with valid email found for GroupProfile %s",
                    group_profile.title,
                )
                return Response(
                    {
                        "error": "No managers with valid email found for this group. "
                        "Please contact the system administrator."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            with transaction.atomic():
                role_request = RoleChangeRequest.objects.create(
                    user=user,
                    group_profile=group_profile,
                    group_role=requested_role,
                    motivazione=motivation,
                )

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=manager_emails,
                    fail_silently=False,
                )

            logger.info(
                "Membership request sent successfully. "
                "User: %s, Group: %s, "
                "Role: %s, Managers notified: %d",
                user.username,
                group_profile.title,
                requested_role,
                len(manager_emails),
            )

            return Response(
                {
                    "success": True,
                    "message": "Membership request sent successfully.",
                    "details": {
                        "group_profile": group_profile.title,
                        "requested_role": role_label,
                        "managers_notified": len(manager_emails),
                        "request_id": role_request.id,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error processing request: %s", str(e), exc_info=True)
            return Response(
                {"message": "Error processing request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GroupProfileListAPIView(APIView):
    """
    API to retrieve the list of all existing GroupProfiles.

    Returns basic information about all available groups in the system,
    including ID, title, description, slug and access level.

    No authentication is required to allow users to view available groups.
    """

    permission_classes = []
    throttle_classes = []

    @swagger_auto_schema(
        operation_description="Retrieve the list of all existing GroupProfiles"
        " with basic information including members count,"
        " managers count, and dashboard information. No authentication required.",
        responses={
            200: openapi.Response(
                description="List of all GroupProfiles retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "count": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Total number of groups",
                        ),
                        "groups": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "title": openapi.Schema(type=openapi.TYPE_STRING),
                                    "slug": openapi.Schema(type=openapi.TYPE_STRING),
                                    "description": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "access": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        description="Group access level",
                                        enum=["public", "public-invite", "private"],
                                    ),
                                    "email": openapi.Schema(type=openapi.TYPE_STRING),
                                    "logo": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        nullable=True,
                                        description="URL to group logo",
                                    ),
                                    "members_count": openapi.Schema(
                                        type=openapi.TYPE_INTEGER
                                    ),
                                    "managers_count": openapi.Schema(
                                        type=openapi.TYPE_INTEGER
                                    ),
                                    "created": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format=openapi.FORMAT_DATETIME,
                                        nullable=True,
                                    ),
                                    "last_modified": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format=openapi.FORMAT_DATETIME,
                                        nullable=True,
                                    ),
                                    "dashboard_id": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        nullable=True,
                                        description="ID of published dashboard if available",
                                    ),
                                },
                            ),
                        ),
                    },
                ),
            ),
            500: openapi.Response(description="Failed to retrieve group profiles"),
        },
    )
    def get(self, request):
        """
        Handle GET request to retrieve all GroupProfiles.
        """
        try:
            # Retrieve all GroupProfiles ordered by title
            group_profiles = GroupProfile.objects.all().order_by("title")

            # Prepare data to return
            groups_data = []
            for group in group_profiles:
                # Count total members
                total_members = GroupMember.objects.filter(group=group).count()

                # Count total managers
                total_managers = GroupMember.objects.filter(
                    group=group, role="manager"
                ).count()

                dashboard = GeoApp.objects.filter(
                    group=group.group, is_published=True
                ).first()

                groups_data.append(
                    {
                        "id": group.id,
                        "title": group.title,
                        "slug": group.slug,
                        "description": group.description or "",
                        "access": group.access,  # 'public', 'public-invite', 'private'
                        "email": group.email or "",
                        "logo": group.logo.url if group.logo else None,
                        "members_count": total_members,
                        "managers_count": total_managers,
                        "created": group.created.isoformat() if group.created else None,
                        "last_modified": (
                            group.last_modified.isoformat()
                            if group.last_modified
                            else None
                        ),
                        "dashboard_id": dashboard.id if dashboard else None,
                    }
                )

            logger.info(
                "List of %d GroupProfiles returned successfully", len(groups_data)
            )

            return Response(
                {"success": True, "count": len(groups_data), "groups": groups_data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(
                "Failed to retrieve group profiles: %s", str(e), exc_info=True
            )
            return Response(
                {"message": "Failed to retrieve group profiles."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
