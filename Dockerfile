FROM ghcr.io/smart-shaped/geonode_keycloak:v1.1.1

RUN mkdir -p /usr/src/farmtech

RUN apt-get update -y && apt-get install curl wget unzip gnupg2 locales -y

RUN sed -i -e 's/# C.UTF-8 UTF-8/C.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# add bower and grunt command
COPY src /usr/src/farmtech/
COPY example_excels /mnt/volumes/example_excels
WORKDIR /usr/src/farmtech

RUN chmod +x /usr/src/farmtech/tasks.py \
    && chmod +x /usr/src/farmtech/entrypoint.sh

RUN yes w | pip install --src /usr/src -r requirements.txt &&\
    yes w | pip install -e .

# Cleanup apt update lists
RUN apt-get autoremove --purge &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/*

# Export ports
EXPOSE 8000
