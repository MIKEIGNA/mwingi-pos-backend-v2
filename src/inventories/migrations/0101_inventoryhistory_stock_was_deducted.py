# Generated by Django 4.0.8 on 2024-01-08 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0100_stocklevel_last_change_source_reg_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryhistory',
            name='stock_was_deducted',
            field=models.BooleanField(default=False, verbose_name='stock was deducted'),
        ),
    ]