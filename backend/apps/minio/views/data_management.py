from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
import logging
from .processing_chains import ProcessingChainInvoker
from apps.core.models import ProcessingChain, RawDataset, Experiment
from apps.minio.serializers import MinioEventSerializer, SuccessResponseSerializer, ErrorResponseSerializer


logger = logging.getLogger(__name__)
type_mapping = {
    'image/tiff': 'tiff',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'excel',
    'text/csv': 'csv',
}

@extend_schema(
    operation_id="minio_webhook",
    summary="MinIO S3 Event Webhook",
    description="Endpoint to receive S3 event notifications from MinIO.",
    tags=["MinIO"],
    request=MinioEventSerializer,
    responses={
        200: OpenApiResponse(
            response=SuccessResponseSerializer,
            description="Webhook processed successfully",
            examples=[
                OpenApiExample(
                    name="Success",
                    summary="Success response",
                    value={"status": "success"},
                    response_only=True,
                )
            ],
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Invalid webhook data",
            examples=[
                OpenApiExample(
                    name="ValidationError",
                    summary="Validation error example",
                    value={"Records": ["This field is required."]},
                    response_only=True,
                )
            ],
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Server error during processing (e.g. processing chain invocation failure)",
            examples=[
                OpenApiExample(
                    name="ProcessingError",
                    summary="Processing chain invocation failed",
                    value={"error": "Processing chain invocation failed"},
                    response_only=True,
                )
            ],
        ),
    },
    examples=[
        OpenApiExample(
            name="S3 Object Created",
            description="Esempio di webhook per creazione oggetto S3",
            value={
                "EventName": "s3:ObjectCreated:Put",
                "Key": "farmtech/azione_2/raw_data/tiff/example-file.tif",
                "Records": [
                    {
                        "eventVersion": "2.0",
                        "eventSource": "minio:s3",
                        "awsRegion": "",
                        "eventTime": "2025-09-25T08:54:03.493Z",
                        "eventName": "s3:ObjectCreated:Put",
                        "userIdentity": {
                            "principalId": "minioadmin"
                        },
                        "requestParameters": {
                            "principalId": "minioadmin",
                            "region": "",
                            "sourceIPAddress": "172.20.0.1"
                        },
                        "responseElements": {
                            "x-amz-id-2": "dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8",
                            "x-amz-request-id": "18687A96F58894AB",
                            "x-minio-deployment-id": "ff905a6c-597b-4682-a392-2d6350aac10f",
                            "x-minio-origin-endpoint": "http://172.20.0.4:9000"
                        },
                        "s3": {
                            "s3SchemaVersion": "1.0",
                            "configurationId": "Config",
                            "bucket": {
                                "name": "farmtech",
                                "ownerIdentity": {
                                    "principalId": "minioadmin"
                                },
                                "arn": "arn:aws:s3:::farmtech"
                            },
                            "object": {
                                "key": "example-file.tif",
                                "size": 12583412,
                                "eTag": "9bd0d3271db8b3d1728734d0af6e2974",
                                "contentType": "image/tiff",
                                "userMetadata": {
                                    "content-type": "image/tiff"
                                },
                                "sequencer": "18687A970291C507"
                            }
                        },
                        "source": {
                            "host": "172.20.0.1",
                            "port": "",
                            "userAgent": "MinIO (linux; amd64) minio-go/v7.0.90"
                        }
                    }
                ]
            },
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def minio_webhook(request):
    
    """
    Endpoint to receive S3 event notifications from MinIO.
    It validates the incoming data, creates a RawDataset entry, and invokes the appropriate processing chain.
    Args:
        request (Request): The incoming HTTP request containing the S3 event data.
    Returns:
        Response: A DRF Response object with the status of the operation.
    Raises:
        ValidationError: If the incoming data is invalid.
    """
    
    logger.info('MinIO webhook called')
    # Validate incoming data
    serializer = MinioEventSerializer(data=request.data)
    logger.info(f"Data: {request.data}")
    if serializer.is_valid():
        # Manage the event as needed
        
        # Extract relevant data
        validated_data = serializer.validated_data
        file_name = validated_data['Key'].split('/')[-1]
        file_path = validated_data['Key'].split('/', 1)[1].replace("/" + file_name, '')
        upload_date = validated_data['Records'][0]['eventTime']
        upload_user = validated_data['Records'][0]['userIdentity']['principalId']
        try:
            file_type = type_mapping[validated_data['Records'][0]['s3']['object']['contentType']]
        except KeyError:
            logger.error('Unsupported file type: %s', validated_data['Records'][0]['s3']['object']['contentType'])
            return Response({'error': 'Unsupported file type'}, status=status.HTTP_400_BAD_REQUEST)
        experiment_name = file_path.split('/', 1)[0]
        file_path_suffix = file_path.split('/', 1)[1] if '/' in file_path else ''
        # Validate load folder structure
        experiment = Experiment.objects.filter(name=experiment_name).first()
        if not experiment or file_path_suffix == '':
            logger.error('Wrong file path: %s or experiment: %s', file_path_suffix, experiment_name)
            return Response({'error': 'Wrong file path or experiment'}, status=status.HTTP_400_BAD_REQUEST)
        # check if file is uploaded in the right folder
        if file_type not in file_path_suffix:
            logger.error('File type %s does not match file path %s', file_type, file_path_suffix)
            return Response({'error': 'File type does not match file path'}, status=status.HTTP_400_BAD_REQUEST)
        # Find the right processing chain
        processing_id = ProcessingChain.objects.filter(experiment=experiment, path=file_path_suffix).first()
        if not processing_id and file_type != 'tiff':
            logger.error('No processing chain found for experiment: %s and path: %s', experiment_name, file_path_suffix)
            return Response({'error': 'No processing chain found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create RawDataset entry
        raw_dataset = RawDataset.objects.create(
            name=file_name,
            path=file_path,
            upload_date=upload_date,
            upload_user=upload_user,
            type=file_type,
            processing_id=processing_id
        )
        raw_dataset.save()
        logger.info('RawDataset created with ID: %s', raw_dataset.id)
        
        # Apply processing chain
        try:
            ProcessingChainInvoker(raw_dataset, processing_id.processing_method if processing_id else 'process_tiff').invoke()
        except Exception as e:
            logger.error('Processing chain invocation failed for RawDataset ID: %s, Error: %s', raw_dataset.id, e)
            return Response({'error': 'Processing chain invocation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    else:
        logger.error('MinIO webhook invalid: %s', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
