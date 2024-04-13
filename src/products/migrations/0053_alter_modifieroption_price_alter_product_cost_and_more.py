# Generated by Django 4.0.8 on 2023-12-12 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0052_alter_modifieroption_price_alter_product_cost_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modifieroption',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, verbose_name='price'),
        ),
        migrations.AlterField(
            model_name='product',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, verbose_name='price'),
        ),
        migrations.AlterField(
            model_name='product',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, max_digits=30, verbose_name='tax rate'),
        ),
        migrations.AlterField(
            model_name='productcount',
            name='cost',
            field=models.DecimalField(decimal_places=2, max_digits=30, verbose_name='cost'),
        ),
        migrations.AlterField(
            model_name='productcount',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=30, verbose_name='price'),
        ),
    ]
