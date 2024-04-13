#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    #python manage.py flush --no-input
    python manage.py migrate;
    python manage.py createcachetable;
    python manage.py create_periodic_task;
    python manage.py manage_createsuperuser; 
    python manage.py cmd_clear_logs page_critical.log;
    python manage.py cmd_clear_logs page_views.log;
    python manage.py runserver 0.0.0.0:8000 & celery -A traqsale_cloud worker -l info \
    & celery -A traqsale_cloud beat -l INFO --pidfile= --scheduler django_celery_beat.schedulers:DatabaseScheduler

    echo "PostgreSQL started"
fi



exec "$@"