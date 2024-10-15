#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

sudo chown -R "${CONTAINER_USER}:${CONTAINER_USER}" /app

# Create superuser
python << END
import django
from django.contrib.auth import get_user_model

# Set the settings module for the Django project
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pbi_manager.settings'

# Initialize Django
django.setup()

User = get_user_model()
username = "${ADMIN_NAME}"
password = "${ADMIN_PASS}"
email = "${ADMIN_EMAIL}"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END

# Start the Django development server
python manage.py runserver 0.0.0.0:8000