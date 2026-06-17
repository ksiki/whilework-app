#!/bin/bash
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn core.asgi:application --bind 0.0.0.0:8000 -w 2 -k uvicorn.workers.UvicornWorker --max-requests 1000 --max-requests-jitter 50