# Generated by Django 3.2 on 2021-08-30 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0029_product_variant_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_bundle',
            field=models.BooleanField(default=False, verbose_name='is bundle'),
        ),
    ]