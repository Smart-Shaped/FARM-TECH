FROM ubuntu:25.10

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

COPY ./styles /init/styles
#COPY ./processed_datasets /init/processed_datasets
COPY ./setup.sh /init/setup.sh

RUN chmod +x /init/setup.sh

ENTRYPOINT ["/init/setup.sh"]
