# Generated by Django 4.0.8 on 2023-11-08 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0073_receiptline_store_reg_no_receiptline_user_reg_no_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='changed_stock',
            field=models.BooleanField(default=True, verbose_name='changed stock'),
        ),
    ]