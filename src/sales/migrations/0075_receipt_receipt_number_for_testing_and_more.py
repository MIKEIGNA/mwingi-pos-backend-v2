# Generated by Django 4.0.8 on 2023-11-08 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0074_receipt_changed_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='receipt_number_for_testing',
            field=models.CharField(default='', max_length=30, verbose_name='receipt_number_for_testing'),
        ),
        migrations.AlterField(
            model_name='receiptline',
            name='product_name',
            field=models.CharField(default='', max_length=100, verbose_name='product name'),
        ),
        migrations.AlterField(
            model_name='receiptline',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='tax rate'),
        ),
    ]