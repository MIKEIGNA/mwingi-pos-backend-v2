# Generated by Django 4.0.8 on 2023-09-13 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0066_purchaseorder_increamental_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorycount',
            name='increamental_id',
            field=models.IntegerField(default=0, verbose_name='increamental id'),
        ),
    ]
