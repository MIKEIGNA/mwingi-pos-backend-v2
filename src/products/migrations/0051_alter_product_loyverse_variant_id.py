# Generated by Django 4.0.8 on 2023-11-05 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0050_product_production_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='loyverse_variant_id',
            field=models.UUIDField(blank=True, db_index=True, null=True, verbose_name='loyverse variant id'),
        ),
    ]