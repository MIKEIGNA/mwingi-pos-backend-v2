# Generated by Django 4.0.8 on 2023-11-15 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0087_inventoryvaluationline_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryvaluationline',
            name='product_reg_no',
            field=models.BigIntegerField(default=0, editable=False, verbose_name='product reg no'),
        ),
        migrations.AlterField(
            model_name='inventoryvaluationline',
            name='store_reg_no',
            field=models.BigIntegerField(default=0, editable=False, verbose_name='store reg no'),
        ),
    ]