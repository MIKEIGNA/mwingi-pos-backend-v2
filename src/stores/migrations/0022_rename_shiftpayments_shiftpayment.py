# Generated by Django 3.2 on 2022-01-05 05:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0021_auto_20220105_0419'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ShiftPayments',
            new_name='ShiftPayment',
        ),
    ]