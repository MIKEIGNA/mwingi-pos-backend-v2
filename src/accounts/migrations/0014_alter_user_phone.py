# Generated by Django 4.0.8 on 2023-09-20 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_user_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.BigIntegerField(default=0, unique=True, verbose_name='phone'),
        ),
    ]