# Generated by Django 3.2 on 2021-11-05 14:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0033_product_minimum_stock_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='minimum_stock_level',
        ),
    ]
