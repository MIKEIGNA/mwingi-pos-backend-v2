# Generated by Django 4.0.8 on 2023-11-28 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_alter_user_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='last name'),
        ),
    ]
