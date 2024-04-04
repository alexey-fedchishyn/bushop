#! /bin/bash

sleep 5

python3 manage.py makemigrations borcivky

python3 manage.py migrate

gunicorn -b 0.0.0.0:8000 bu.wsgi:application