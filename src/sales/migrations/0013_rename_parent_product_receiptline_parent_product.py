# Generated by Django 3.2 on 2021-09-22 09:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0012_auto_20210922_0946'),
    ]

    operations = [
        migrations.RenameField(
            model_name='receiptline',
            old_name='parent_Product',
            new_name='parent_product',
        ),
    ]