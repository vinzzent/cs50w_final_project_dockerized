#!/bin/bash

# if any of the commands in your code fails for any reason, the entire script fails
set -o errexit
# fail exit if one of your pipe command fails
set -o pipefail
# exits if any of your variables is not set
set -o nounset

postgres_ready() {
    python << END
import sys
import psycopg2

try:
    psycopg2.connect(
        dbname="${SQL_DATABASE}",
        user="${SQL_USER}",
        password="${SQL_PASSWORD}",
        host="${SQL_HOST}",
        port="${SQL_PORT}",
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

# Wait until PostgreSQL is available
until postgres_ready; do
    >&2 echo 'Waiting for PostgreSQL to become available...'
    sleep 1
done
>&2 echo 'PostgreSQL is available'

# Check if the command is start.sh
if [[ "${1:-}" == "/start.sh" ]]; then
    >&2 echo "Running migrations..."
    python manage.py makemigrations
    python manage.py migrate
    python manage.py populate_activity_fields
fi

exec "$@"