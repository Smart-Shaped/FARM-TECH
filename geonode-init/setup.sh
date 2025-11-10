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

curl --location 'http://geoserver:8080/geoserver/rest/workspaces/geonode/styles' \
    --header 'Content-Type: application/vnd.ogc.sld+xml' \
    --header "Authorization: Basic ${GEOSERVER_AUTH_STRING}" \
    --data-binary '@/init/styles/NDVI_True_color.xml'

echo -e "\nFinished"

echo -e ""

# uploading all datasets
echo -e "Uploading processed datasets to GeoNode..."

for dataset in /init/processed_datasets/*/*; do
    echo -e "\nUploading $dataset to GeoNode..."
    curl --location 'http://django:8000/api/v2/uploads/upload' \
        --header "Authorization: Basic ${GEONODE_AUTH_STRING}" \
        --form "base_file=@\"$dataset\"" \
        --form 'skip_existing_layers="true"' \
        --form 'overwrite_existing_layer="true"'
    echo -e ""
done

echo -e "\nFinished uploading datasets."
