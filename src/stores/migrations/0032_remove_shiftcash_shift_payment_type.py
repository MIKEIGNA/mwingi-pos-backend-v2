# Generated by Django 3.2 on 2022-01-14 07:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0031_auto_20220113_1602'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shiftcash',
            name='shift_payment_type',
        ),
    ]