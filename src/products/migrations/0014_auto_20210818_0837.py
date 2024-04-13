# Generated by Django 3.2 on 2021-08-18 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_auto_20210810_1313'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sold_each',
            field=models.BooleanField(default=True, verbose_name='sold each'),
        ),
        migrations.AlterField(
            model_name='product',
            name='barcode',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='barcode'),
        ),
        migrations.AlterField(
            model_name='product',
            name='bundles',
            field=models.ManyToManyField(blank=True, to='products.ProductBundle'),
        ),
        migrations.AlterField(
            model_name='product',
            name='modifiers',
            field=models.ManyToManyField(blank=True, to='products.Modifier'),
        ),
        migrations.AlterField(
            model_name='product',
            name='variants',
            field=models.ManyToManyField(blank=True, to='products.ProductVariant'),
        ),
    ]
