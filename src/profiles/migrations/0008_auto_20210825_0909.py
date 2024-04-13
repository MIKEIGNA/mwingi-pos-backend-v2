# Generated by Django 3.2 on 2021-08-25 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_remove_customer_store'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='company',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='location',
        ),
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.CharField(default='', max_length=100, verbose_name='address'),
        ),
        migrations.AddField(
            model_name='customer',
            name='city',
            field=models.CharField(default='', max_length=100, verbose_name='city'),
        ),
        migrations.AddField(
            model_name='customer',
            name='country',
            field=models.CharField(default='', max_length=50, verbose_name='country'),
        ),
        migrations.AddField(
            model_name='customer',
            name='customer_code',
            field=models.CharField(default='', max_length=50, verbose_name='customer code'),
        ),
        migrations.AddField(
            model_name='customer',
            name='name',
            field=models.CharField(default='', max_length=100, verbose_name='name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='customer',
            name='postal_code',
            field=models.CharField(default='', max_length=50, verbose_name='postal code'),
        ),
        migrations.AddField(
            model_name='customer',
            name='region',
            field=models.CharField(default='', max_length=100, verbose_name='region'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(default='', max_length=30, verbose_name='email'),
        ),
    ]