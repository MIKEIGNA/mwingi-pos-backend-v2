# Generated by Django 3.2 on 2021-09-23 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0019_alter_receipt_item_couut'),
    ]

    operations = [
        migrations.RenameField(
            model_name='receipt',
            old_name='item_couut',
            new_name='item_count',
        ),
    ]
