# Generated by Django 4.0.8 on 2023-07-11 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0044_customer_village_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='village_name',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='village name'),
        ),
    ]