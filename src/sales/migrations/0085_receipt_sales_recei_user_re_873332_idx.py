# Generated by Django 4.0.8 on 2023-12-12 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0084_receipt_store_reg_no_receipt_user_reg_no'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='receipt',
            index=models.Index(fields=['user_reg_no', 'store_reg_no', 'created_date'], name='sales_recei_user_re_873332_idx'),
        ),
    ]
