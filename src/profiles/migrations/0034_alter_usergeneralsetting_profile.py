# Generated by Django 3.2 on 2022-01-04 12:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0033_usergeneralsetting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergeneralsetting',
            name='profile',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='profiles.profile'),
        ),
    ]