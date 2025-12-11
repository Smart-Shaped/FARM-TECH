"""
Celery signals for FarmTech application.
"""

import os
import logging
import json
import requests
from celery.signals import task_postrun
from django.contrib.auth.models import Group
from geonode.security.permissions import PermSpec, PermSpecCompact
from geonode.resource.api.tasks import resouce_service_dispatcher
from geonode.groups.models import GroupProfile
from geonode.layers.models import Dataset
from geonode.resource.models import ExecutionRequest

from farmtech.models import DatasetExperiment


logger = logging.getLogger("celery")

__DATASET_PATH = "/usr/src/farmtech/resources/datasets.json"
__DATASET_EXPERIMENT_PATH = "/usr/src/farmtech/resources/datasets_experiment.json"


def manage_tif_style(resource):
    """
    Apply specific styles to multi-spectral raster datasets in GeoServer.
    This function checks if the resource is a multi-spectral raster (indicated by the title
    starting with 'ms_') and applies predefined styles to it in GeoServer.
    It also updates the database to associate the styles with the corresponding dataset.
    5-bands raster styles applied: NDVI, True_color, Negative_true_color.
    Args:
        resource: The GeoNode resource object representing the dataset.
    Raises:
        ValueError: If the dataset is not found or if the GeoServer update fails.
    """

    if resource.title.startswith("ms_") and resource.subtype == "raster":

        logger.info("Managing style for resource: %s", resource)

        logger.info("Adding bound between style and dataset to database.")
        dataset = Dataset.objects.filter(id=resource.id).first()
        if dataset:
            dataset.styles.clear()
            dataset.styles.add(1)
            dataset.styles.add(1000)
            dataset.styles.add(1001)
            dataset.save()
        else:
            raise ValueError(f"Dataset not found for resource: {resource}")

        logger.info("Adding style to GeoServer layer.")

        body = {
            "layer": {
                "styles": {
                    "@class": "linked-hash-set",
                    "style": [
                        {
                            "name": "geonode:NDVI",
                            "workspace": "geonode",
                            "href": "http://localhost/geoserver/rest/workspaces/geonode/styles/NDVI.json",
                        },
                        {
                            "name": "geonode:True_color",
                            "workspace": "geonode",
                            "href": "http://localhost/geoserver/rest/workspaces/geonode/styles/True_color.json",
                        },
                        {
                            "name": "geonode:Negative_true_color",
                            "workspace": "geonode",
                            "href": "http://localhost/geoserver/rest/workspaces/geonode/styles/Negative_true_color.json",
                        },
                    ],
                }
            }
        }

        url = f"http://geoserver:8080/geoserver/rest/layers/{resource.alternate}"

        response = requests.put(
            url,
            json=body,
            timeout=10,
            auth=(
                os.environ.get("GEOSERVER_ADMIN_USER", "admin"),
                os.environ.get("GEOSERVER_ADMIN_PASSWORD", "geoserver"),
            ),
            headers={"Content-Type": "application/json"},
        )

        if response.status_code not in [200, 201]:
            logger.error(
                "Failed to update GeoServer layer styles for resource: %s, status code: %s, response: %s",
                resource,
                response.status_code,
                response.text,
            )
            raise ValueError(
                f"Failed to update GeoServer layer styles for resource: {resource}"
            )

        logger.info("Style applied for resource: %s", resource)


@task_postrun.connect
def after_imported_resource(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra
):
    """
    Celery signal handler for post-processing after a resource import task.
    This function listens for the completion of the 'importer.create_geonode_resource' task.
    Upon successful completion, it associates the imported resource with the appropriate user group
    and applies specific styles for multi-spectral raster datasets.
    """

    task_name = getattr(sender, "name", sender)
    logger.info("Task name: %s", task_name)

    if task_name == "importer.create_geonode_resource":
        logger.info("Farmtech: Detected finished resource import task.")

        try:
            if isinstance(retval, (list, tuple)) and len(retval) == 2:
                _, execution_id = retval
                logger.info("Execution ID: %s", execution_id)

                exec_req = ExecutionRequest.objects.filter(exec_id=execution_id).first()
                if exec_req:
                    resource = exec_req.geonode_resource
                    logger.info("Imported resource: %s (%s)", resource, resource.uuid)

                    user = resource.owner
                    if not user:
                        return

                    group_profile = GroupProfile.objects.filter(
                        groupmember__user=user
                    ).first()
                    if group_profile:
                        group = group_profile.group
                        resource.group = group
                        resource.save()
                    else:
                        with open(__DATASET_PATH, encoding="utf-8") as f:
                            datasets = json.load(f)
                        resource.group = Group.objects.get(id=datasets[resource.title])
                        resource.is_published = True
                        resource.is_approved = True
                        resource.advertised = True
                        resource.save()

                        # dataset_experiment

                        new_groups_perms = {
                            "anonymous": ["view_resourcebase"],
                            "registered-members": [
                                "view_resourcebase",
                                "download_resourcebase",
                            ],
                            str(resource.group.name): [
                                "view_resourcebase",
                                "download_resourcebase",
                            ],
                        }
                        json_perms = resource.get_all_level_info()
                        json_perms["groups"] = new_groups_perms
                        logger.info(str(json_perms))
                        perms_spec = PermSpec(json_perms, resource)
                        perms_spec_compact = PermSpecCompact(
                            perms_spec.compact, resource
                        )

                        _exec_request = ExecutionRequest.objects.create(
                            user=user,
                            func_name="set_permissions",
                            geonode_resource=resource,
                            action="permissions",
                            input_params={
                                "uuid": resource.uuid,
                                "owner": user.username,
                                "permissions": perms_spec_compact.extended,
                                "created": False,
                            },
                        )
                        resouce_service_dispatcher.apply_async(
                            args=(str(_exec_request.exec_id),), expiration=30
                        )

                    create_dataset_experiment(resource)
                    # manage 5-bands raster style
                    manage_tif_style(resource)

        except Exception as e:
            logger.exception("Error in farmtech import handler: %s", e)


def create_dataset_experiment(resource):
    """
    Create a DatasetExperiment object for the given resource.
    """
    if resource.subtype == "vector":

        with open(__DATASET_EXPERIMENT_PATH, encoding="utf-8") as f:
            datasets = json.load(f)
            model_package = datasets[resource.title]["model_package"]
            template_path = datasets[resource.title]["template_path"]

        dataset_experiment = DatasetExperiment()
        dataset_experiment.model_package = model_package
        dataset_experiment.template_path = template_path
        dataset = Dataset.objects.get(uuid=resource.uuid)
        dataset_experiment.layer_dataset = dataset
        group_profile = GroupProfile.objects.get(group=resource.group)
        dataset_experiment.group_profile = group_profile
        dataset_experiment.save()
