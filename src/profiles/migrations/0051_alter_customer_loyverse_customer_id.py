# Generated by Django 4.0.8 on 2023-09-05 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0050_customer_loyverse_customer_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='loyverse_customer_id',
            field=models.UUIDField(blank=True, db_index=True, editable=False, null=True, verbose_name='loyverse customer id'),
        ),
    ]
