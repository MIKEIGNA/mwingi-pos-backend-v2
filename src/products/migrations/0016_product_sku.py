# Generated by Django 3.2 on 2021-08-18 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_auto_20210818_0843'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='sku'),
        ),
    ]
