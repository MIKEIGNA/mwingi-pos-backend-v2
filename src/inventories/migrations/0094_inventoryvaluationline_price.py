# Generated by Django 4.0.8 on 2023-12-20 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0093_alter_inventorycountline_cost_difference_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryvaluationline',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=30, verbose_name='price'),
        ),
    ]