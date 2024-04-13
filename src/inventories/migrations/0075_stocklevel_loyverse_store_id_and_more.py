# Generated by Django 4.0.8 on 2023-09-29 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0074_remove_productdisassemblyline_purchase_cost_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocklevel',
            name='loyverse_store_id',
            field=models.UUIDField(blank=True, db_index=True, editable=False, null=True, verbose_name='loyverse store id'),
        ),
        migrations.AddField(
            model_name='stocklevel',
            name='loyverse_variant_id',
            field=models.UUIDField(blank=True, db_index=True, editable=False, null=True, verbose_name='loyverse variant id'),
        ),
    ]
