# Generated by Django 3.2 on 2021-08-10 09:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_auto_20210810_0909'),
    ]

    operations = [
        migrations.RenameField(
            model_name='modifieroptions',
            old_name='modifer',
            new_name='modifier',
        ),
    ]
