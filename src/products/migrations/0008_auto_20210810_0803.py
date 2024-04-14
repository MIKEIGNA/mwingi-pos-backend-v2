# Generated by Django 3.2 on 2021-08-10 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0011_alter_category_color_code'),
        ('products', '0007_rename_modifers_product_modifiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='modifier',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='price'),
        ),
        migrations.AddField(
            model_name='modifier',
            name='stores',
            field=models.ManyToManyField(to='stores.Store'),
        ),
    ]