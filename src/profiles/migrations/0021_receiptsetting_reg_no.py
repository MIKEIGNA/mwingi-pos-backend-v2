# Generated by Django 3.2 on 2021-11-02 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0020_receiptsetting_store'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiptsetting',
            name='reg_no',
            field=models.BigIntegerField(default=0, editable=False, unique=True, verbose_name='reg no'),
        ),
    ]