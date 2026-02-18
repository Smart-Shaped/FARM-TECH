"""
Views for dataset operations: updating datasets from Excel files,
retrieving Excel templates for groups, and downloading templates.
"""

import datetime
import logging
import os
import uuid
import pandas as pd
import geopandas
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.utils.module_loading import import_string
from django.http import FileResponse, Http404
from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from shapely.geometry import Point
from geonode.layers.models import Dataset
from geonode.groups.models import GroupProfile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from farmtech.authentication import KeycloakAuthentication
from farmtech.models import DatasetExperiment, RawFile
from farmtech.serializers import DatasetUpdateSerializer, GroupExcelTemplatesSerializer
from farmtech.permissions import IsGroupProfileMember
from ..utils.user_utils import get_area_groups


logger = logging.getLogger(__name__)


def _series_to_kwargs(series: pd.Series) -> dict:
    """
    Convert a pandas Series to a dictionary of keyword arguments.
    Handles missing values, datetime conversions, numpy scalars,
    float-to-int conversions, and string stripping.

    Args:
        series: The pandas Series to convert.

    Returns:
        dict: The converted dictionary of keyword arguments.
    """

    kwargs = {}
    for col, v in series.items():
        # handle missing
        if pd.isna(v):
            kwargs[col] = None
            continue

        # numpy scalar -> python scalar
        if isinstance(v, np.generic):
            try:
                v = v.item()
            except Exception:
                pass

        # float that is actually an integer value -> int
        if isinstance(v, float) and v.is_integer():
            kwargs[col] = int(v)
            continue

        # strip strings
        if isinstance(v, str):
            kwargs[col] = v.strip()
            continue

        if isinstance(v, Point):
            point_wkt = v.wkt
            v = GEOSGeometry(point_wkt)

        # fallback: pass as-is (often int, bool)
        kwargs[col] = v

    return kwargs


class DatasetUpdateAPIView(APIView):
    """
    API to update a dataset with data from an Excel file.

    Flow:
    1. Receive the dataset name and an Excel file
    2. Find the dataset in the layers_dataset table
    3. Find the corresponding DatasetExperiment to get the model_package
    4. Load the data from the Excel file into the specific model

    Requires the user to be a member of the GroupProfile associated with the DatasetExperiment.
    """

    authentication_classes = [SessionAuthentication, KeycloakAuthentication]
    permission_classes = [IsAuthenticated, IsGroupProfileMember]

    @swagger_auto_schema(
        operation_description="Update a dataset with data from an Excel file. The Excel file is validated and inserted into the corresponding model based on the DatasetExperiment configuration.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["dataset_name", "excel_file"],
            properties={
                "dataset_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the dataset to update",
                ),
                "excel_file": openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description="Excel file containing the data to insert (.xlsx or .xls)",
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="Data inserted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid input data or Excel file format error"
            ),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(
                description="Permission denied - user must be a member of the GroupProfile"
            ),
            404: openapi.Response(description="Dataset or DatasetExperiment not found"),
            500: openapi.Response(
                description="Error during processing or writing to model"
            ),
        },
    )
    def post(self, request):
        """
        Handle POST request to update dataset from Excel file.
        """

        serializer = DatasetUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        dataset_name = serializer.validated_data["dataset_name"]
        excel_file = serializer.validated_data["excel_file"]

        try:
            # Find the dataset in layers_dataset table
            try:
                dataset = Dataset.objects.get(name=dataset_name)
                logger.info("Dataset found: %s (ID: %s)", dataset.name, dataset.id)
            except Dataset.DoesNotExist:
                return Response(
                    {"error": f"Dataset with name '{dataset_name}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Find the corresponding DatasetExperiment to extract the model_package
            try:
                dataset_experiment = DatasetExperiment.objects.get(
                    layer_dataset=dataset
                )
                model_package = dataset_experiment.model_package
                logger.info("DatasetExperiment found. Model package: %s", model_package)
            except DatasetExperiment.DoesNotExist:
                return Response(
                    {
                        "error": f"No DatasetExperiment found for dataset '{dataset_name}'"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            self.check_object_permissions(request, dataset_experiment)

            if not model_package:
                return Response(
                    {"error": "Model package not found in DatasetExperiment"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Load the model from the model_package
            try:
                model_class = import_string(model_package)
                logger.info("Model loaded: %s", model_class.__name__)
            except (ValueError, LookupError) as e:
                logger.exception(
                    "Error loading model package '%s': %s",
                    model_package,
                    str(e),
                    exc_info=True,
                )
                return Response(
                    {"error": f"Invalid model package '{model_package}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Read the data from the Excel file into a DataFrame
            try:
                df = pd.read_excel(excel_file)
                df.columns = [
                    col.strip()
                    .lower()
                    .replace("-", "_")
                    .replace(" ", "_")
                    .replace("/", "__")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("°", "gradi_")
                    .replace("%", "perc")
                    .replace("#", "number")
                    for col in df.columns
                ]

                date_columns = [col for col in df.columns if col.startswith("dat")]

                for col in date_columns:
                    df[col] = pd.to_datetime(
                        df[col], format="%d/%m/%Y", errors="coerce"
                    ).dt.date

                logger.info(
                    "Excel file read. Roes: %s, Columns: %s", len(df), len(df.columns)
                )
            except Exception as e:
                logger.exception("Error reading Excel file: %s", str(e), exc_info=True)
                return Response(
                    {"message": "Error reading Excel file."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # check if the dataframe has a geometry column
            if "geometry" not in df.columns and (
                "lat" not in df.columns and "long" not in df.columns
            ):
                return Response(
                    {"error": "Excel file does not contain a 'geometry' column"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "lat" in df.columns and "long" in df.columns:
                df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
                df["long"] = pd.to_numeric(df["long"], errors="coerce")
                df.dropna(subset=["lat", "long"], inplace=True)

                # 1. Create a shapely Point object for each row
                df["geometry"] = df.apply(
                    lambda row: Point(row["long"], row["lat"]), axis=1
                )
                df = geopandas.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
                df = df.drop(columns=["lat", "long"])

            # Create a folder for the raw file
            folder_path = "/mnt/volumes/statics/upserts"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            upsert_path = os.path.join(folder_path, str(uuid.uuid4()))
            if not os.path.exists(upsert_path):
                os.makedirs(upsert_path)

            with open(os.path.join(upsert_path, excel_file.name), "wb") as file:
                file.write(excel_file.read())

            raw_file = RawFile.objects.create(
                name=excel_file.name,
                path=upsert_path,
                upload_datetime=datetime.datetime.now(),
                type="excel",
                status="processing",
                user=request.user,
                dataset_experiment=dataset_experiment,
            )
            raw_file.save()

            logger.info("Read dataframe: %s rows, %s columns", len(df), len(df.columns))
            logger.info("Writing to model %s...", model_class.__name__)

            # Create records to add to model table
            try:
                records = []
                for _, row in df.iterrows():
                    kwargs = _series_to_kwargs(row)
                    print(kwargs)
                    record = model_class(**kwargs)
                    records.append(record)

                model_class.objects.bulk_create(records)
            except Exception as e:
                logger.exception("Error writing to model: %s", str(e), exc_info=True)
                raw_file.status = "failed"
                raw_file.save()
                return Response(
                    {"error": "Error writing to model"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            logger.info("Finished writing to model %s", model_class.__name__)

            raw_file.status = "processed"
            raw_file.save()

            # Response
            response_data = {
                "success": True,
                "message": f"Data inserted successfully into {model_class.__name__}",
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception("Error during processing: %s", str(e), exc_info=True)
            return Response(
                {"error": "Error during processing the request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GroupExcelTemplatesAPIView(APIView):
    """
    API to retrieve the list of Excel templates for a GroupProfile.

    Returns the DatasetExperiment associated with the GroupProfile with:
    - URL for downloading the template
    - Datetime of the last upload process

    Requires the user to be authenticated as a member of the GroupProfile.
    """

    authentication_classes = [SessionAuthentication, KeycloakAuthentication]
    permission_classes = [IsAuthenticated, IsGroupProfileMember]

    @swagger_auto_schema(
        operation_description="Retrieve the list of Excel templates for a GroupProfile with download URLs and last upload information.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["group_profile_id"],
            properties={
                "group_profile_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the GroupProfile",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="List of Excel templates retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "group_profile": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "title": openapi.Schema(type=openapi.TYPE_STRING),
                                "slug": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        "templates_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "templates": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "dataset_experiment_id": openapi.Schema(
                                        type=openapi.TYPE_INTEGER
                                    ),
                                    "dataset_name": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "filename": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "download_url": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "last_upload_datetime": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format=openapi.FORMAT_DATETIME,
                                        nullable=True,
                                    ),
                                    "last_upload_id": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        nullable=True,
                                    ),
                                    "last_upload_user": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        nullable=True,
                                    ),
                                },
                            ),
                        ),
                    },
                ),
            ),
            400: openapi.Response(description="Invalid input data"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(
                description="Permission denied - user must be a member of the GroupProfile"
            ),
            404: openapi.Response(
                description="GroupProfile not found or no datasets found for the group"
            ),
            500: openapi.Response(description="Error retrieving Excel templates"),
        },
    )
    def post(self, request):
        """
        Handle POST request to get Excel templates for a GroupProfile.
        """
        serializer = GroupExcelTemplatesSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        group_profile_id = serializer.validated_data["group_profile_id"]

        try:
            # Find the GroupProfile
            try:
                group_profile = GroupProfile.objects.get(id=group_profile_id)
                logger.info(
                    "GroupProfile found: %s (ID: %s)",
                    group_profile.title,
                    group_profile.id,
                )
            except GroupProfile.DoesNotExist:
                return Response(
                    {"error": f"GroupProfile with ID '{group_profile_id}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            self.check_object_permissions(request, group_profile)

            # Get all DatasetExperiment for this GroupProfile
            dataset_experiments = DatasetExperiment.objects.filter(
                group_profile=group_profile
            ).select_related("layer_dataset")

            # Build response with download URLs and last upload datetime
            templates = []
            if dataset_experiments.exists():
                for dataset_exp in dataset_experiments:
                    if not dataset_exp.template_path:
                        logger.warning(
                            "DatasetExperiment %s has no template_path", dataset_exp.id
                        )
                        continue

                    # Extract filename from template_path
                    filename = os.path.basename(dataset_exp.template_path)

                    # Find the most recent RawFile for this dataset_experiment with status='processed'
                    last_upload = (
                        RawFile.objects.filter(
                            dataset_experiment=dataset_exp,
                            status="processed",
                            type="excel",
                        )
                        .order_by("-upload_datetime")
                        .first()
                    )

                    # Build download URL using dataset_experiment ID
                    download_url = f"/api/dataset/download-template/{dataset_exp.id}"

                    template_info = {
                        "dataset_experiment_id": dataset_exp.id,
                        "dataset_name": dataset_exp.layer_dataset.name,
                        "filename": filename,
                        "download_url": download_url,
                    }

                    if last_upload:
                        template_info["last_upload_datetime"] = (
                            last_upload.upload_datetime.isoformat()
                        )
                        template_info["last_upload_id"] = last_upload.id
                        template_info["last_upload_user"] = last_upload.user.username
                    else:
                        template_info["last_upload_datetime"] = None
                        template_info["last_upload_id"] = None
                        template_info["last_upload_user"] = None

                    templates.append(template_info)

                # Sort by filename
                templates.sort(key=lambda x: x["filename"])

            logger.info(
                "Found %d templates for group '%s'", len(templates), group_profile.title
            )

            response_data = {
                "success": True,
                "group_profile": {
                    "id": group_profile.id,
                    "title": group_profile.title,
                    "slug": group_profile.slug,
                },
                "templates_count": len(templates),
                "templates": templates,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Error retrieving Excel templates: %s", str(e), exc_info=True
            )
            return Response(
                {"message": "Error retrieving Excel templates."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownloadExcelTemplateAPIView(APIView):
    """
    API per scaricare un file Excel template tramite DatasetExperiment ID.

    URL: /api/dataset/download-template/<dataset_experiment_id>

    Restituisce il file Excel come download usando il template_path dal DatasetExperiment.

    Requires the user to be a member of the GroupProfile associated with the DatasetExperiment.
    """

    authentication_classes = [
        SessionAuthentication,
        KeycloakAuthentication,
    ]
    permission_classes = [IsAuthenticated, IsGroupProfileMember]

    @swagger_auto_schema(
        operation_description="Download an Excel template file for a specific DatasetExperiment.",
        manual_parameters=[
            openapi.Parameter(
                "dataset_experiment_id",
                openapi.IN_PATH,
                description="ID of the DatasetExperiment",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                description="Excel template file download",
                schema=openapi.Schema(
                    type=openapi.TYPE_FILE,
                ),
            ),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(
                description="Permission denied - user must be a member of the GroupProfile"
            ),
            404: openapi.Response(
                description="DatasetExperiment not found, template not configured, or file not found"
            ),
        },
    )
    def get(self, request, dataset_experiment_id):
        """
        Handle GET request to download Excel template for a DatasetExperiment.
        """
        try:
            # Find the DatasetExperiment
            try:
                dataset_exp = DatasetExperiment.objects.select_related(
                    "group_profile"
                ).get(id=dataset_experiment_id)
                logger.info("DatasetExperiment found: ID %s", dataset_exp.id)
            except DatasetExperiment.DoesNotExist as e:
                raise Http404(
                    "DatasetExperiment with ID " f"'{dataset_experiment_id}' not found"
                ) from e

            self.check_object_permissions(request, dataset_exp)

            # Check if template_path exists
            if not dataset_exp.template_path:
                raise Http404("No template file configured for this dataset")

            file_path = dataset_exp.template_path

            logger.info("Attempting to download file: %s", file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                raise Http404(f"Template file not found at path: {file_path}")

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(file_path):
                raise Http404(f"Template path is not a valid file: {file_path}")

            # Extract filename
            filename = os.path.basename(file_path)

            # Validate file extension
            if not filename.lower().endswith((".xlsx", ".xls")):
                raise Http404(f"Template is not a valid Excel file: {filename}")

            # Open the file and return as download
            file_handle = open(file_path, "rb")
            response = FileResponse(
                file_handle,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(
                "Template '%s' downloaded successfully by user '%s' (DatasetExperiment: %s)",
                filename,
                request.user.username,
                dataset_exp.id,
            )

            return response

        except Http404:
            raise
        except Exception as e:
            logger.exception(
                "Error downloading Excel template: %s", str(e), exc_info=True
            )
            raise Http404(f"Error downloading file: {str(e)}") from e


@login_required
@permission_required("farmtech.uploader", raise_exception=True)
def uploader_view(request):
    """
    View for the uploader page - allows to download Excel templates and upload data
    Templates are dynamically retrieved via API
    """
    area_groups = get_area_groups(request.user)

    user_uploads = RawFile.objects.filter(user=request.user).order_by(
        "-upload_datetime"
    )

    context = {"uploads": user_uploads, "user_groups": area_groups}

    return render(request, "uploader.html", context)
