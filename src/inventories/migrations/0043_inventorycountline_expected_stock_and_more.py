# Generated by Django 4.0.8 on 2023-07-02 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0042_rename_expected_stock_stockadjustmentline_counted_stock_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorycountline',
            name='expected_stock',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='expected stock'),
        ),
        migrations.AlterField(
            model_name='stockadjustment',
            name='reason',
            field=models.IntegerField(choices=[(0, 'Receive items'), (1, 'Loss'), (2, 'Damage')], verbose_name='reason'),
        ),
    ]
