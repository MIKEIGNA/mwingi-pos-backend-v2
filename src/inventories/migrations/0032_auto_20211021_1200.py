# Generated by Django 3.2 on 2021-10-21 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0031_auto_20211021_1141'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaseorder',
            name='total',
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='order_completed',
            field=models.BooleanField(default=False, verbose_name='order completed'),
        ),
    ]
