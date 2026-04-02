#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
# Make sure whitenoise is configured in settings.py for this to work
python manage.py collectstatic --no-input
