# Generated by Django 4.2.8 on 2024-01-31 05:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventories", "0103_purchaseorderline_synced_with_tally_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventoryvaluationline",
            name="is_recaclulated",
            field=models.BooleanField(default=False, verbose_name="is recaclulated"),
        ),
    ]
