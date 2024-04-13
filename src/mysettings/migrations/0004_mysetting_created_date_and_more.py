# Generated by Django 4.0.8 on 2024-01-16 12:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mysettings', '0003_alter_mysetting_receipt_change_stock_task_running'),
    ]

    operations = [
        migrations.AddField(
            model_name='mysetting',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date'),
        ),
        migrations.AlterField(
            model_name='mysetting',
            name='receipt_change_stock_task_running',
            field=models.BooleanField(default=False, verbose_name='stock task running'),
        ),
    ]