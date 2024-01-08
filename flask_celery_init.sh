#!/bin/bash

gunicorn --bind 0.0.0.0:4000 --worker-class eventlet -w 1 app:app &
celery -A app.celery worker -l info -E --pool eventlet &
wait -n
exit $?