"""
View to monitor the status of upload tasks in the Celery queue.
"""

from celery import current_app
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser


@api_view(['GET'])
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
                if not name_filter or name_filter in (t.get('name') or ''):
                    total += 1
        return total
    name_filter = 'importer.import_orchestrator'
    running = count_tasks(active, name_filter)
    queued = count_tasks(reserved, name_filter)
    return Response({'running': running, 'queued': queued, 'pending_total': running + queued})
