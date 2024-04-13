# Generated by Django 4.0.8 on 2023-09-25 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0051_store_is_store'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='store',
            name='is_store',
        ),
        migrations.AddField(
            model_name='store',
            name='is_shop',
            field=models.BooleanField(default=False, verbose_name='is shop'),
        ),
    ]
