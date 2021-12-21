#!/bin/bash

VENV=./venv

if [ ! -d $VENV ]; then
    python -m venv $VENV
    $VENV/bin/pip install -U pip
fi


$VENV/bin/pip install -r requirements_develop.txt

$VENV/bin/coverage run --omit 'venv/*' --source='.' manage.py test

$VENV/bin/coverage report

echo '\nFLAKE8\n'

$VENV/bin/flake8 --exclude=venv,migrations,tests --max-line-length=120 ./

