# Generated by Django 4.0.8 on 2023-11-26 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0089_remove_inventoryvaluation_margin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryvaluationline',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20, verbose_name='cost'),
        ),
    ]
