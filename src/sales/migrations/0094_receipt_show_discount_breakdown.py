# Generated by Django 4.2.8 on 2024-03-26 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0093_alter_receipt_loyverse_store_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='show_discount_breakdown',
            field=models.BooleanField(default=False, verbose_name='show_discount_breakdown'),
        ),
    ]
