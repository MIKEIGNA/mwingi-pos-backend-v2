# Generated by Django 3.2 on 2021-11-05 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0038_remove_purchaseorder_received'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocklevel',
            name='status',
            field=models.IntegerField(choices=[(0, 'In stock'), (1, 'Low stock'), (2, 'Out of stock')], default=0, verbose_name='status'),
        ),
    ]
