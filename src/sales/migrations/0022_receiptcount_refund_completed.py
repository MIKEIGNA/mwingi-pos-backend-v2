# Generated by Django 3.2 on 2021-09-24 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0021_alter_receiptline_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiptcount',
            name='refund_completed',
            field=models.BooleanField(default=False, verbose_name='refund completed'),
        ),
    ]
