# Generated by Django 3.2 on 2021-10-04 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0016_stockadjustment_stockadjustmentline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stocklevel',
            name='units',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='units'),
        ),
    ]
