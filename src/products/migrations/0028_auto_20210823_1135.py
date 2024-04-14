# Generated by Django 3.2 on 2021-08-23 11:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_remove_customer_store'),
        ('products', '0027_modifier_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='modifier',
            name='profile',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='profiles.profile'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='modifier',
            name='description',
            field=models.CharField(default='', max_length=100, verbose_name='description'),
        ),
    ]