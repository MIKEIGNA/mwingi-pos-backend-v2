# Generated by Django 3.2 on 2022-02-22 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0037_alter_storeshift_all_refunds_during_shift'),
        ('sales', '0053_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='payment_type',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='stores.storepaymentmethod'),
            preserve_default=False,
        ),
    ]