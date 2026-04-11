#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# This collects all your CSS/JS into one folder for production
python manage.py collectstatic --no-input

# This creates your tables in the Render Database
python manage.py migrate