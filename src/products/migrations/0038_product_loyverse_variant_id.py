# Generated by Django 4.0.8 on 2023-09-05 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0037_product_tax_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='loyverse_variant_id',
            field=models.UUIDField(db_index=True, default=0, editable=False, verbose_name='loyverse variant id'),
            preserve_default=False,
        ),
    ]