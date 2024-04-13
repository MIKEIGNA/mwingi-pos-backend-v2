# Generated by Django 4.0.8 on 2023-11-08 17:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0076_receiptline_sync_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='receiptline',
            name='sync_date',
        ),
        migrations.AddField(
            model_name='receipt',
            name='sync_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='sync date'),
        ),
    ]