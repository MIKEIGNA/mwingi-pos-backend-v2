# Generated by Django 3.2 on 2021-08-23 14:48

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stores', '0012_auto_20210818_0837'),
        ('firebase', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FirebaseDevicee',
            new_name='FirebaseDevice',
        ),
    ]