#!/bin/bash

BUCKET_NAME=$BUCKET_NAME
WEBHOOK_URL=$WEBHOOK_URL
MINIO_URL=${MINIO_URL:-http://minio:9000}

echo "Creating MinIO alias..."
mc alias set myminio $MINIO_URL ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin}

echo "Creating MinIO bucket..."
mc mb myminio/$BUCKET_NAME || echo "Bucket already exists."

echo "Configuring webhook..."
mc admin config set myminio notify_webhook:1 endpoint="$WEBHOOK_URL" queue_limit="10"

echo "Reboot MinIO service..."
mc admin service restart myminio --json

echo "Waiting for MinIO to be ready..."
sleep 10

echo "Configuring MinIO events..."
mc event add myminio/$BUCKET_NAME arn:minio:sqs::1:webhook --event put,delete

echo "MinIO setup completed."
