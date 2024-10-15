FROM python:3.12-slim-bookworm

# Ensure output is immediately displayed and bytecode is not written to disk
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Arguments for the container's user and password
ARG CONTAINER_USER
ARG CONTAINER_PASSWORD

# Update package lists and install necessary build tools and dependencies
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    git \
    sudo && \
  apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Create a non-root user, set password, and configure sudo
RUN useradd -m -d /app -s /bin/bash ${CONTAINER_USER} && \
  echo "${CONTAINER_USER}:${CONTAINER_PASSWORD}" | chpasswd && \
  echo "${CONTAINER_USER} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
  usermod -aG sudo ${CONTAINER_USER}

# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY ./compose/local/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./compose/local/django/start.sh /start.sh
RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh

COPY ./compose/local/django/celery/worker/start.sh /start-celeryworker.sh
RUN sed -i 's/\r$//g' /start-celeryworker.sh
RUN chmod +x /start-celeryworker.sh

COPY ./compose/local/django/celery/beat/start.sh /start-celerybeat.sh
RUN sed -i 's/\r$//g' /start-celerybeat.sh
RUN chmod +x /start-celerybeat.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]