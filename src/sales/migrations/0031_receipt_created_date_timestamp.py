# Generated by Django 3.2 on 2021-09-27 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0030_remove_receipt_created_date_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='created_date_timestamp',
            field=models.BigIntegerField(default=0, editable=False, verbose_name='created date timestamp'),
        ),
    ]
