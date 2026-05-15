#!/bin/bash
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000