# Generated by Django 3.2 on 2021-11-01 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0018_customer_current_debt'),
        ('sales', '0033_remove_receipt_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='profile',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='profiles.profile'),
            preserve_default=False,
        ),
    ]
