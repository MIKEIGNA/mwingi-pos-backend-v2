# Generated by Django 4.0.8 on 2023-10-06 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0081_producttransformline_is_reverse_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttransformline',
            name='added_quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='added quantity'),
        ),
        migrations.AlterField(
            model_name='producttransformline',
            name='is_reverse',
            field=models.BooleanField(default=False, verbose_name='is reverse'),
        ),
    ]