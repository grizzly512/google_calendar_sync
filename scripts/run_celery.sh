#!/usr/bin/env bash

VENV=./venv

# Waiting for Django
sleep 5

while [ -f /opt/google_calendar_sync/deploy_state.flag ];
do
    sleep 1;
    echo "Wait for django"
done;

if [[ $1 == "limited" ]]; then
    $VENV/bin/celery worker -E -A google_calendar_sync.celery -c $MAX_PARALEL_COMPANY_SYNK -l info -n sync_company -Q sync_company
elif [[ $1 == "sync" ]]; then
    $VENV/bin/celery worker -E -A google_calendar_sync.celery -l info -n sync -Q sync
else
    echo "Run celery beat"
    if [[ -f celerybeat.pid ]]; then rm celerybeat.pid; fi
    if [[ -f celerybeat-schedule ]]; then rm celerybeat-schedule; fi
    $VENV/bin/celery beat -A google_calendar_sync.celery -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
fi