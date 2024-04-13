# Generated by Django 3.2.12 on 2023-07-26 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0053_inventoryhistory_change_source_desc_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryhistory',
            name='product_name',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='product name'),
        ),
        migrations.AddField(
            model_name='inventoryhistory',
            name='store_name',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='store name'),
        ),
        migrations.AddField(
            model_name='inventoryhistory',
            name='user_name',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='user name'),
        ),
        migrations.AlterField(
            model_name='inventoryhistory',
            name='change_source_desc',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='change source desc'),
        ),
        migrations.AlterField(
            model_name='inventoryhistory',
            name='change_source_reg_no',
            field=models.BigIntegerField(default=0, editable=False, verbose_name='change source reg no'),
        ),
    ]
