FROM continuumio/miniconda3:25.3.1-1

RUN apt-get update && \
    apt-get install -y \
    curl \
    gcc \
    git \
    libpq-dev \
    openssh-server && \
    apt-get clean

WORKDIR /app

ENV PYTHONPATH=/app/projects

ENV METAFLOW_USER=docker_user

# Install python dependencies
COPY environment.yml environment.yml

RUN conda env create --file /app/environment.yml

ENV PATH=/opt/conda/envs/venv/bin:$PATH

RUN echo "conda activate venv" >> ~/.bashrc

SHELL ["/bin/bash", "--login", "-c"]

EXPOSE 8888

# clone chaM3Leon repository
RUN git clone https://github.com/Smart-Shaped/chaM3Leon.git && \
    cd chaM3Leon && \
    git checkout dev-python-library-integration && \
    git pull && \
    pip install .

WORKDIR /app

# setup ssh
RUN mkdir /var/run/sshd && \
    echo 'root:password' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    ssh-keygen -A

EXPOSE 22

COPY entrypoint.sh .

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
