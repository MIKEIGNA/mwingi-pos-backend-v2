# Generated by Django 4.0.8 on 2023-07-04 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0047_transferorderline_reg_no_alter_transferorder_reg_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorderline',
            name='reg_no',
            field=models.BigIntegerField(editable=False, verbose_name='reg no'),
        ),
        migrations.AlterField(
            model_name='transferorder',
            name='reg_no',
            field=models.BigIntegerField(editable=False, unique=False, verbose_name='reg no'),
        ),
    ]
