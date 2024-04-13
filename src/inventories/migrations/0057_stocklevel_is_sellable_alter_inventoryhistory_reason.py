# Generated by Django 4.0.8 on 2023-07-31 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0056_inventorycount_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocklevel',
            name='is_sellable',
            field=models.BooleanField(default=True, verbose_name='is sellable'),
        ),
        migrations.AlterField(
            model_name='inventoryhistory',
            name='reason',
            field=models.IntegerField(choices=[(0, 'Sale'), (1, 'Refund'), (2, 'Receive'), (3, 'Receive'), (4, 'Transfer'), (5, 'Inventory count'), (6, 'Damage'), (7, 'Loss'), (8, 'Production'), (9, 'Item edit')], default=0, verbose_name='reason'),
        ),
    ]