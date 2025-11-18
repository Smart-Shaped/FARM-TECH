mkdir ml_runner/ssh
ssh-keygen -t rsa -b 4096 -f ./ml_runner/ssh/id_rsa_django -N ""

mkdir geonode-init/processed_datasets

cd src/farmtech/client/js
npm i
npm run build

cd ../../../..
docker compose build
docker compose up -d
