# Generated by Django 4.0.8 on 2023-09-15 08:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0046_productproductionmap_reg_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productproductionmap',
            name='reg_no',
        ),
    ]