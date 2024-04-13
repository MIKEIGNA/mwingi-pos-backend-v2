# Generated by Django 3.2 on 2021-08-10 07:04

import accounts.utils.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image_color',
        ),
        migrations.AddField(
            model_name='product',
            name='color_code',
            field=models.CharField(default='#474A49', max_length=7, validators=[accounts.utils.validators.validate_code], verbose_name='color code'),
        ),
    ]
