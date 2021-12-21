#!/bin/bash

VENV=./venv
DEPLOY_FLAG=/opt/google_calendar_sync/deploy_state.flag


touch $DEPLOY_FLAG

if [ ! -d $VENV ]; then
    python -m venv $VENV
    $VENV/bin/pip install -U pip
fi


$VENV/bin/pip install -r requirements.txt


$VENV/bin/python manage.py migrate
$VENV/bin/python manage.py collectstatic --no-input

rm -f $DEPLOY_FLAG

echo "Run Django"

$VENV/bin/gunicorn google_calendar_sync.wsgi:application --bind 0.0.0.0:8000
