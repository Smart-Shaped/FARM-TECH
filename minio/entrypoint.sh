#!/bin/bash

set -e

BUCKET_NAME=$BUCKET_NAME
WEBHOOK_URL=$WEBHOOK_URL
MINIO_URL=${MINIO_URL:-http://minio:9000}

echo "Waiting for MinIO to be ready..."
until mc alias set myminio $MINIO_URL ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin} 2>/dev/null; do
  echo "MinIO not ready yet, waiting..."
  sleep 2
done

echo "MinIO is ready! Creating MinIO alias..."
mc alias set myminio $MINIO_URL ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin}

echo "Creating MinIO bucket..."
mc mb myminio/$BUCKET_NAME || echo "Bucket already exists."

# Function to create folder if it doesn't exist
create_folder_if_not_exists() {
    local folder_path=$1
    if ! mc ls myminio/$folder_path > /dev/null 2>&1; then
        echo "Creating folder: $folder_path"
        mc mb myminio/$folder_path
    else
        echo "Folder already exists: $folder_path"
    fi
}

echo "Creating folders in the bucket..."
create_folder_if_not_exists "$BUCKET_NAME/experiment_1/raw_data/excel"
create_folder_if_not_exists "$BUCKET_NAME/experiment_2/raw_data/tiff"
create_folder_if_not_exists "$BUCKET_NAME/experiment_3/raw_data/excel"
create_folder_if_not_exists "$BUCKET_NAME/experiment_4/raw_data/excel"
create_folder_if_not_exists "$BUCKET_NAME/experiment_4/raw_data/tiff"
create_folder_if_not_exists "$BUCKET_NAME/experiment_5/raw_data/csv"
create_folder_if_not_exists "$BUCKET_NAME/zootechnical_experiment/raw_data/excel"

echo "Configuring webhook..."
mc admin config set myminio notify_webhook:1 endpoint="$WEBHOOK_URL" queue_limit="10"

echo "Creating MinIO policies for Keycloak integration..."

# Policy di sola lettura
cat > /tmp/readonly.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}/*",
        "arn:aws:s3:::${BUCKET_NAME}"
      ]
    }
  ]
}
EOF

# Policy di lettura/scrittura
cat > /tmp/readwrite.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}/*",
        "arn:aws:s3:::${BUCKET_NAME}"
      ]
    }
  ]
}
EOF

# Policy admin console (accesso completo)
cat > /tmp/consoleAdmin.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "admin:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": [
        "arn:aws:s3:::*"
      ]
    }
  ]
}
EOF

# Policy per data scientist (accesso agli esperimenti)
cat > /tmp/datascientist.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}/experiment_*/*",
        "arn:aws:s3:::${BUCKET_NAME}/zootechnical_experiment/*",
        "arn:aws:s3:::${BUCKET_NAME}"
      ]
    }
  ]
}
EOF

# Applica le policy
echo "Applying MinIO policies..."
mc admin policy create myminio readonly /tmp/readonly.json 2>/dev/null || echo "Policy 'readonly' already exists"
mc admin policy create myminio readwrite /tmp/readwrite.json 2>/dev/null || echo "Policy 'readwrite' already exists"
mc admin policy create myminio consoleAdmin /tmp/consoleAdmin.json 2>/dev/null || echo "Policy 'consoleAdmin' already exists"
mc admin policy create myminio datascientist /tmp/datascientist.json 2>/dev/null || echo "Policy 'datascientist' already exists"

# Cleanup temporary files
rm -f /tmp/readonly.json /tmp/readwrite.json /tmp/consoleAdmin.json /tmp/datascientist.json

echo "Reboot MinIO service..."
mc admin service restart myminio --json

echo "Waiting for MinIO to be ready..."
sleep 10

echo "Configuring MinIO events..."
mc event add myminio/$BUCKET_NAME arn:minio:sqs::1:webhook --event put || echo "Event already configured"

echo "MinIO setup completed successfully!"
echo ""
echo "Available policies for Keycloak users:"
echo "  - readonly: Read-only access to bucket"
echo "  - readwrite: Read/Write access to bucket"
echo "  - datascientist: Read/Write access to experiment folders"
echo "  - consoleAdmin: Full admin access"
