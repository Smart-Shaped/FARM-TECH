from rest_framework import serializers
from rest_framework import serializers as drf_serializers


class UserIdentitySerializer(serializers.Serializer):
    
    principalId = serializers.CharField()

class RequestParametersSerializer(serializers.Serializer):
    
    principalId = serializers.CharField()
    region = serializers.CharField(allow_blank=True)
    sourceIPAddress = serializers.IPAddressField()

class ResponseElementsSerializer(serializers.Serializer):
    
    x_amz_id_2 = serializers.CharField(source="x-amz-id-2")
    x_amz_request_id = serializers.CharField(source="x-amz-request-id")
    x_minio_deployment_id = serializers.CharField(source="x-minio-deployment-id")
    x_minio_origin_endpoint = serializers.URLField(source="x-minio-origin-endpoint")
    
    def to_internal_value(self, data):
        mapped_data = {
            'x_amz_id_2': data.get('x-amz-id-2'),
            'x_amz_request_id': data.get('x-amz-request-id'),
            'x_minio_deployment_id': data.get('x-minio-deployment-id'),
            'x_minio_origin_endpoint': data.get('x-minio-origin-endpoint'),
        }
        return super().to_internal_value(mapped_data)

class OwnerIdentitySerializer(serializers.Serializer):
    
    principalId = serializers.CharField()

class BucketSerializer(serializers.Serializer):
    
    name = serializers.CharField()
    ownerIdentity = OwnerIdentitySerializer()
    arn = serializers.CharField()

class UserMetadataSerializer(serializers.Serializer):
    
    content_type = serializers.CharField(source="content-type")
    
    def to_internal_value(self, data):
        mapped_data = {
            'content_type': data.get('content-type'),
        }
        return super().to_internal_value(mapped_data)

class ObjectSerializer(serializers.Serializer):
    
    key = serializers.CharField()
    size = serializers.IntegerField()
    eTag = serializers.CharField()
    contentType = serializers.CharField()
    userMetadata = UserMetadataSerializer()
    sequencer = serializers.CharField()

class S3Serializer(serializers.Serializer):
    
    s3SchemaVersion = serializers.CharField()
    configurationId = serializers.CharField()
    bucket = BucketSerializer()
    object = ObjectSerializer()

class SourceSerializer(serializers.Serializer):
    
    host = serializers.CharField()
    port = serializers.CharField(allow_blank=True)
    userAgent = serializers.CharField()

class RecordSerializer(serializers.Serializer):
    
    eventVersion = serializers.CharField()
    eventSource = serializers.CharField()
    awsRegion = serializers.CharField(allow_blank=True)
    eventTime = serializers.DateTimeField()
    eventName = serializers.CharField()
    userIdentity = UserIdentitySerializer()
    requestParameters = RequestParametersSerializer()
    responseElements = ResponseElementsSerializer()
    s3 = S3Serializer()
    source = SourceSerializer()

class MinioEventSerializer(serializers.Serializer):
    
    EventName = serializers.CharField()
    Key = serializers.CharField()
    Records = RecordSerializer(many=True)

# Small helper serializers used only for documenting responses
class SuccessResponseSerializer(drf_serializers.Serializer):
    status = drf_serializers.CharField()


class ErrorResponseSerializer(drf_serializers.Serializer):
    # Represent a typical serializer.errors shape for documentation
    Records = drf_serializers.ListField(child=drf_serializers.CharField(), required=False)
    