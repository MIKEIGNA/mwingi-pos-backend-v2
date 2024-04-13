# Generated by Django 4.0.8 on 2023-12-12 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0090_inventoryvaluationline_cost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producttransformline',
            name='added_quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name='added quantity'),
        ),
        migrations.AlterField(
            model_name='producttransformline',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name='amount'),
        ),
        migrations.AlterField(
            model_name='producttransformline',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='producttransformline',
            name='quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20, verbose_name='quantity'),
        ),
    ]