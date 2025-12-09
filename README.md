# T4Y_repo

## Setup steps

### Create .env file

Run the following command to create .env file, it must be then populated manually with the required values for Keycloak and Copernicus API.

```bash
python create-envfile.py
```

### Enable SSH communication

Run the following command before docker compose build command to generate SSH key pair, without generating a passphrase:

```bash
mkdir ml_runner/ssh
ssh-keygen -t rsa -b 4096 -f ./ml_runner/ssh/id_rsa_django
```

### Populate geonode datasets

Before building, create the following folder and move the geojson and tiff files inside.

```bash
mkdir geonode-init/processed_datasets
```

### Run npm build

Install npm dependencies, it requires nodejs.

```bash
cd src/farmtech/client/js
npm i
npm run build
```

### Docker

Build the Docker images and run the containers.

```bash
docker compose build
docker compose up -d
```
