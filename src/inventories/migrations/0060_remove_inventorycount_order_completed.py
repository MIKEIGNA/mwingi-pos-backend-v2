# Generated by Django 4.0.8 on 2023-08-21 11:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0059_inventorycount_order_completed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorycount',
            name='order_completed',
        ),
    ]
