# Generated by Django 3.2 on 2021-09-26 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0028_customerdebt_customerdebtcount'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='local_reg_no',
            field=models.BigIntegerField(default=0, verbose_name='local reg no'),
        ),
    ]
