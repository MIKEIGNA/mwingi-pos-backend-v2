# Generated by Django 3.2.12 on 2023-09-05 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0051_alter_customer_loyverse_customer_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=30, null=True, verbose_name='email'),
        ),
    ]