#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for commands to be executed..."

    python manage.py collectstatic --no-input; 
    python manage.py migrate;
    python manage.py createcachetable;
    python manage.py manage_createsuperuser; 
    python manage.py create_periodic_task;
    python manage.py cmd_clear_logs page_critical.log;
    python manage.py cmd_clear_logs page_views.log;
    daphne -b 0.0.0.0 -p 8000 traqsale_cloud.asgi:application & \
    celery -A traqsale_cloud worker -l info & \
    celery -A traqsale_cloud beat -l INFO --pidfile= --scheduler django_celery_beat.schedulers:DatabaseScheduler
    
    echo "Finished executing commands to be executed..."
fi

exec "$@"
