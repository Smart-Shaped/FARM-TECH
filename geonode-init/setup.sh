#!/bin/bash
echo -e "Setting up Geoserver styles..."

# Set default credentials if environment variables are not set
GEOSERVER_ADMIN_USER=${GEOSERVER_ADMIN_USER:-admin}
GEOSERVER_ADMIN_PASSWORD=${GEOSERVER_ADMIN_PASSWORD:-geoserver}
GEONODE_ADMIN_USER=${ADMIN_USERNAME:-admin}
GEONODE_ADMIN_PASSWORD=${ADMIN_PASSWORD:-geonode}

# Create proper base64 encoded credentials
GEOSERVER_AUTH_STRING=$(echo -n "${GEOSERVER_ADMIN_USER}:${GEOSERVER_ADMIN_PASSWORD}" | base64)
GEONODE_AUTH_STRING=$(echo -n "${GEONODE_ADMIN_USER}:${GEONODE_ADMIN_PASSWORD}" | base64)

for style_file in /init/styles/*.xml; do
    style_name=$(basename "$style_file" .xml)
    echo -e "\nUploading style $style_name to GeoServer..."
    curl --location 'http://geoserver:8080/geoserver/rest/workspaces/geonode/styles' \
        --header 'Content-Type: application/vnd.ogc.sld+xml' \
        --header "Authorization: Basic ${GEOSERVER_AUTH_STRING}" \
        --data-binary "@$style_file"
    echo -e ""
done

echo -e ""

# uploading all datasets
echo -e "Uploading processed datasets to GeoNode..."
MAX_CONCURRENT_TASKS=${MAX_CONCURRENT_TASKS:-5}
SLEEP_BETWEEN_UPLOADS=${SLEEP_BETWEEN_UPLOADS:-5}
STATUS_URL="http://django:8000/api/queues/uploads-status"

wait_for_capacity() {
  while true; do
    resp=$(curl --location "$STATUS_URL" --header "Authorization: Basic ${GEONODE_AUTH_STRING}" || echo '{}')
    pending=$(echo "$resp" | jq -r '.pending_total // 0')
    if [ "$pending" -lt "$MAX_CONCURRENT_TASKS" ]; then
      break
    fi
    echo "Pending tasks $pending >= $MAX_CONCURRENT_TASKS, waiting..."
    sleep $SLEEP_BETWEEN_UPLOADS
  done
}

for dataset in /init/processed_datasets/*/*; do
    wait_for_capacity
    echo -e "\nUploading $dataset to GeoNode..."
    curl --location 'http://django:8000/api/v2/uploads/upload' \
        --header "Authorization: Basic ${GEONODE_AUTH_STRING}" \
        --form "base_file=@\"$dataset\"" \
        --form 'skip_existing_layers="true"' \
        --form 'overwrite_existing_layer="true"'
    echo -e ""
    # wait a bit before sending the next upload to avoid bursts
    sleep $SLEEP_BETWEEN_UPLOADS
done

echo -e "\nFinished uploading datasets."
