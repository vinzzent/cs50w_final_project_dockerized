#!/bin/bash

set -o errexit
set -o nounset

# Remove any existing celerybeat PID file
rm -f './celerybeat.pid'

# Wait for the site to return HTTP status 200 (OK)
SITE_URL="http://web:8000/accounts/login/?next=/"

site_ready() {
    python << END
import sys
import requests

SITE_URL = "${SITE_URL}"

try:
    response = requests.get(SITE_URL)
    if response.status_code == 200:
        sys.exit(0)
except requests.exceptions.RequestException:
    sys.exit(-1)

sys.exit(-1)
END
}

# Wait until the site is available
until site_ready; do
    >&2 echo 'Waiting for the site to become available...'
    sleep 5
done
>&2 echo 'Site is available'

# Start Celery Beat after the site is available
celery -A pbi_manager beat -l INFO