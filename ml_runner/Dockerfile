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
ENV USERNAME=docker_user
ENV METAFLOW_USER=docker_user

# Install python dependencies
COPY . .

RUN conda env create --file /app/environment.yml

ENV PATH=/opt/conda/envs/venv/bin:$PATH

RUN echo "conda activate venv" >> ~/.bashrc

SHELL ["/bin/bash", "--login", "-c"]

EXPOSE 8888

WORKDIR /app

# setup ssh
RUN mkdir /var/run/sshd && \
    echo 'root:password' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
#    ssh-keygen -A

RUN mkdir -p /root/.ssh
COPY ssh/id_rsa_django.pub /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

EXPOSE 22

COPY entrypoint.sh .

RUN chmod +x /app/entrypoint.sh

# managing external dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r /app/requirements.txt

ENTRYPOINT [ "/app/entrypoint.sh" ]
