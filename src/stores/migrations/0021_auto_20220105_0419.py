# Generated by Django 3.2 on 2022-01-05 04:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0020_auto_20220104_1951'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeshift',
            name='gross_sales',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='gross sales'),
        ),
        migrations.AddField(
            model_name='storeshift',
            name='net_sales',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='net sales'),
        ),
    ]
