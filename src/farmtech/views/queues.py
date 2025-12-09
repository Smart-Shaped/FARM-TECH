"""
View to monitor the status of upload tasks in the Celery queue.
"""

from celery import current_app
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


@swagger_auto_schema(
    method="get",
    operation_description="Monitor the status of upload tasks in the Celery queue. Returns the count of running and queued import_orchestrator tasks. Admin access only.",
    responses={
        200: openapi.Response(
            description="Queue status retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "running": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Number of currently running upload tasks",
                    ),
                    "queued": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Number of queued upload tasks waiting to be executed",
                    ),
                    "pending_total": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Total number of pending tasks (running + queued)",
                    ),
                },
            ),
        ),
        401: openapi.Response(description="Authentication required"),
        403: openapi.Response(description="Permission denied - admin access required"),
    },
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def uploads_queue_status(request):
    """
    View to get the status of upload tasks in the Celery queue.
    Returns the number of running and queued upload tasks.
    """

    i = current_app.control.inspect()
    active = i.active() or {}
    reserved = i.reserved() or {}

    # count tasks with name matching your upload task
    def count_tasks(mapping, name_filter=None):
        total = 0
        for worker, tasks in mapping.items():
            for t in tasks:
                if not name_filter or name_filter in (t.get("name") or ""):
                    total += 1
        return total

    name_filter = "importer.import_orchestrator"
    running = count_tasks(active, name_filter)
    queued = count_tasks(reserved, name_filter)
    return Response(
        {"running": running, "queued": queued, "pending_total": running + queued}
    )
