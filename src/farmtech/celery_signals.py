import logging
from celery.signals import task_postrun
from geonode.groups.models import GroupProfile


logger = logging.getLogger("celery")

def manage_tif_style(resource):

    """
    Apply a specific style to multi-spectral raster datasets.
    If the resource title starts with 'ms_' and is of subtype 'raster', 
    it sets the default style to the style with ID 1.
    1 is the style created for 5-bands raster visualization.
    5-bands raster datasets are typically multi-spectral images used in remote sensing applications.
    This function ensures that such datasets are visualized correctly 
    by applying the appropriate style.
    Args:
        resource: The resource object to be styled.
    """

    if resource.title.startswith("ms_") and resource.subtype == "raster":

        logger.info("Managing style for resource: %s", resource)

        from geonode.layers.models import Dataset

        dataset = Dataset.objects.filter(id=resource.id).first()
        if dataset:
            dataset.default_style_id = 1
            dataset.styles.clear()
            dataset.styles.add(1)
            dataset.save()

            logger.info("Style applied for resource: %s", resource)

@task_postrun.connect
def after_imported_resource(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):

    """
    Celery signal handler for post-processing after a resource import task.
    This function listens for the completion of the 'importer.create_geonode_resource' task.
    Upon successful completion, it associates the imported resource with the appropriate user group
    and applies specific styles for multi-spectral raster datasets.
    """

    task_name = getattr(sender, "name", sender)
    logger.info(f"Task name: {task_name}")

    if task_name == "importer.create_geonode_resource":
        logger.info("Farmtech: Detected finished resource import task.")
        try:
            # The return value of importer.create_geonode_resource is (task_name, execution_id)
            if isinstance(retval, (list, tuple)) and len(retval) == 2:
                _, execution_id = retval
                logger.info("Execution ID: %s", execution_id)

                # import geonode models dynamically to avoid circular import
                from geonode.resource.models import ExecutionRequest
                exec_req = ExecutionRequest.objects.filter(exec_id=execution_id).first()
                if exec_req:
                    resource = exec_req.geonode_resource
                    logger.info("Imported resource: %s (%s)", resource, resource.uuid)

                    user = resource.owner
                    if not user:
                        return

                    group_profile = GroupProfile.objects.filter(groupmember__user=user).first()
                    if group_profile:
                        group = group_profile.group
                        resource.group = group
                        resource.save()

                    # manage 5-bands raster style
                    manage_tif_style(resource)

        except Exception as e:
            logger.exception("Error in farmtech import handler: %s", e)
