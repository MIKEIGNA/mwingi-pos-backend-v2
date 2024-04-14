# Generated by Django 4.0.8 on 2023-06-23 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0040_stocklevel_minimum_stock_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockadjustmentline',
            name='expected_stock',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='expected stock'),
        ),
        migrations.AddField(
            model_name='stockadjustmentline',
            name='remove_stock',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='remove stock'),
        ),
    ]