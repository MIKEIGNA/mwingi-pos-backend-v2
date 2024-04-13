# Generated by Django 3.2 on 2021-10-24 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0035_alter_purchaseorder_total_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorycount',
            name='notes',
            field=models.CharField(blank=True, default='', max_length=500, verbose_name='notes'),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='notes',
            field=models.CharField(blank=True, default='', max_length=500, verbose_name='notes'),
        ),
        migrations.AlterField(
            model_name='transferorder',
            name='notes',
            field=models.CharField(blank=True, default='', max_length=500, verbose_name='notes'),
        ),
    ]
