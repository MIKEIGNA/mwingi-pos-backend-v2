# Generated by Django 3.2 on 2021-08-10 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_modifier_modifieroptions'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='modifers',
            field=models.ManyToManyField(to='products.Modifier'),
        ),
    ]
