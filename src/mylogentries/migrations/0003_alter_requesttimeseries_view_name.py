# Generated by Django 4.0.8 on 2023-10-11 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mylogentries', '0002_alter_requesttimeseries_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requesttimeseries',
            name='view_name',
            field=models.CharField(max_length=500, verbose_name='view name'),
        ),
    ]
