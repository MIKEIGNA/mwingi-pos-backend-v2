# Generated by Django 4.0.8 on 2023-07-11 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clusters', '0001_initial'),
        ('profiles', '0041_auto_20220518_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='stores',
            field=models.ManyToManyField(to='clusters.storecluster'),
        ),
    ]
