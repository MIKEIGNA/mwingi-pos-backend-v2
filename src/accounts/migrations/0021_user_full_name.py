# Generated by Django 4.0.8 on 2023-11-05 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_alter_user_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='full_name',
            field=models.CharField(default='', max_length=150, verbose_name='full name'),
            preserve_default=False,
        ),
    ]
