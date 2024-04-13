# Generated by Django 3.2 on 2021-08-28 12:03

import accounts.utils.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0009_auto_20210826_0911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='address',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='address'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='city',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='city'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='name',
            field=models.CharField(max_length=50, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=models.BigIntegerField(blank=True, null=True, validators=[accounts.utils.validators.validate_phone_for_models], verbose_name='phone'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='points',
            field=models.IntegerField(default=0, max_length=10, verbose_name='points'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='region',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='region'),
        ),
    ]