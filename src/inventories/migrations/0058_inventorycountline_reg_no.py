# Generated by Django 4.0.8 on 2023-08-21 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0057_stocklevel_is_sellable_alter_inventoryhistory_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorycountline',
            name='reg_no',
            field=models.BigIntegerField(default=0, editable=False, verbose_name='reg no'),
            preserve_default=False,
        ),
    ]
