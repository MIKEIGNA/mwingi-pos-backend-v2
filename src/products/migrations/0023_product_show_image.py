# Generated by Django 3.2 on 2021-08-20 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_auto_20210819_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='show_image',
            field=models.BooleanField(default=False, verbose_name='show image'),
        ),
    ]