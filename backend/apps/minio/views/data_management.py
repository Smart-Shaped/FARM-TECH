from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
import logging
from apps.minio.serializers import MinioEventSerializer, SuccessResponseSerializer, ErrorResponseSerializer


logger = logging.getLogger(__name__)

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
    },
    examples=[
        OpenApiExample(
            name="S3 Object Created",
            description="Esempio di webhook per creazione oggetto S3",
            value={
                "EventName": "s3:ObjectCreated:Put",
                "Key": "farmtech/example-file.tif",
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
                                "contentType": "application/octet-stream",
                                "userMetadata": {
                                    "content-type": "application/octet-stream"
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
    """
 
    logger.info('MinIO webhook called')
    serializer = MinioEventSerializer(data=request.data)
    if serializer.is_valid():
        # Manage the event as needed
        # TODO insert in DB
        logger.info('MinIO webhook valid: %s', serializer.validated_data)
        
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    else:
        logger.warning('MinIO webhook invalid: %s', serializer.errors)
        # TODO handle invalid data, for example send some kind of notification, or a specific write on DB
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
