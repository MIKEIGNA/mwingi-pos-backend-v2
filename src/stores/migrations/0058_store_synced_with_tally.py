# Generated by Django 4.2.8 on 2024-01-13 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0057_alter_store_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='synced_with_tally',
            field=models.BooleanField(default=False, verbose_name='synced with tally'),
        ),
    ]