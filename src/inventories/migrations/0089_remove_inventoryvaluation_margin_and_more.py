# Generated by Django 4.0.8 on 2023-11-15 12:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0088_alter_inventoryvaluationline_product_reg_no_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventoryvaluation',
            name='margin',
        ),
        migrations.RemoveField(
            model_name='inventoryvaluation',
            name='potential_profit',
        ),
        migrations.RemoveField(
            model_name='inventoryvaluation',
            name='total_inventory_value',
        ),
        migrations.RemoveField(
            model_name='inventoryvaluation',
            name='total_retail_value',
        ),
    ]