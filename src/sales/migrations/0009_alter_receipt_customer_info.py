# Generated by Django 3.2 on 2021-09-22 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0008_receipt_customer_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='customer_info',
            field=models.JSONField(default={}),
        ),
    ]