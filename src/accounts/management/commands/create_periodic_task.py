import pytz

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from django_celery_beat.models import CrontabSchedule, PeriodicTask, IntervalSchedule

from core.db_utils import DbUtils

class Command(BaseCommand):
    """
    To call this command,

    python manage.py create_periodic_task
    """
    help = 'Creates periodic tasks'

    def handle(self, *args, **options):

        # Delate all CrontabSchedule and PeriodicTask to prevent unwanted 
        # collisions duplicates
        CrontabSchedule.objects.all().delete()
        PeriodicTask.objects.all().delete()

        if DbUtils.check_if_we_are_in_production():
            # Creates tasks for production
            self.setup_run_five_minutes_tasks()
            self.setup_local_midnight_tasks()
        
        self.setup_run_thirty_minutes_tasks()
        self.setup_midnight_tasks()
        self.setup_receipt_change_stock_tasks()

        self.stdout.write(
            self.style.SUCCESS('Successfully created periodic tasks')
        )

    def setup_midnight_tasks(self):

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='03',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=pytz.timezone(settings.CELERY_TIMEZONE)
        )

        # Only create task if it does not exist
        periodic_task_name = 'midnight_tasks'
        task_name = 'midnight_tasks'

        PeriodicTask.objects.create(
            crontab=schedule,
            name=periodic_task_name,
            task=task_name,
            start_time=timezone.now()
        )

    def setup_local_midnight_tasks(self):

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='00',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=pytz.timezone(settings.CELERY_TIMEZONE)
        )

        # Only create task if it does not exist
        periodic_task_name = 'local_midnight_tasks'
        task_name = 'local_midnight_tasks'

        PeriodicTask.objects.create(
            crontab=schedule,
            name=periodic_task_name,
            task=task_name,
            start_time=timezone.now()
        )

    def setup_run_hourly_tasks(self):
        """
        Creates an interval schedule for run_hourly_tasks to run 
        every hour.
        """
        periodic_task_name = 'run_hourly_tasks'
        task_name = 'run_hourly_tasks'

        interval, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period='hours'
        )

        PeriodicTask.objects.create(
            interval=interval,
            name=periodic_task_name,
            task=task_name,
            start_time=timezone.now()
        )

    def setup_run_five_minutes_tasks(self):
        """
        Creates an interval schedule for run_five_minutes to run 
        every 5 minutes.
        """
        periodic_task_name = 'five_minutes_tasks'
        task_name = 'five_minutes_tasks'

        interval, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period='minutes'
        )

        PeriodicTask.objects.create(
            interval=interval,
            name=periodic_task_name,
            task=task_name,
            start_time=timezone.now()
        )

    def setup_run_thirty_minutes_tasks(self):
        """
        Creates an interval schedule for run_thirty_minutes_tasks to run 
        every 30 minutes.
        """
        periodic_task_name = 'thirty_minutes_tasks'
        task_name = 'thirty_minutes_tasks'

        interval, _ = IntervalSchedule.objects.get_or_create(
            every=30,
            period='minutes'
        )

        PeriodicTask.objects.create(
            interval=interval,
            name=periodic_task_name,
            task=task_name,
            start_time=timezone.now()
        )

    def setup_receipt_change_stock_tasks(self):
        """
        Creates an interval schedule for receipt_change_stock_tasks to run 
        every hour.
        """
        periodic_task_name = 'receipt_change_stock_tasks'
        task_name = 'receipt_change_stock_tasks'

        interval, _ = IntervalSchedule.objects.get_or_create(
            every=120,
            period='seconds'
        )

        PeriodicTask.objects.create(
            interval=interval,
            name=periodic_task_name,
            task=task_name,
            start_time=timezone.now()
        )



    

    

