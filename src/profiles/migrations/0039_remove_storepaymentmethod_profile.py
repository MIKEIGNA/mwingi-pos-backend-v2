# Generated by Django 3.2 on 2022-02-02 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0038_alter_storepaymentmethod_profile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storepaymentmethod',
            name='profile',
        ),
    ]