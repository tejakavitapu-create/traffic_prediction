#!/usr/bin/env bash
# Exit on error
set -o errexit

# Verify Python version
python3 --version

# Install dependencies
pip install -r requirements.txt

# Run migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files
python3 manage.py collectstatic --no-input
