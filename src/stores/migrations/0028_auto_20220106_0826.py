# Generated by Django 3.2 on 2022-01-06 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0027_storeshift_payments_json'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storeshift',
            name='payments_json',
            field=models.JSONField(default=dict, verbose_name='payments json'),
        ),
        migrations.DeleteModel(
            name='ShiftSalePayment',
        ),
    ]
