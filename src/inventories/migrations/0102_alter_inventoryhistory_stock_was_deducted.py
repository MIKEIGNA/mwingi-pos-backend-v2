# Generated by Django 4.0.8 on 2024-01-08 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0101_inventoryhistory_stock_was_deducted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryhistory',
            name='stock_was_deducted',
            field=models.BooleanField(default=True, verbose_name='stock was deducted'),
        ),
    ]