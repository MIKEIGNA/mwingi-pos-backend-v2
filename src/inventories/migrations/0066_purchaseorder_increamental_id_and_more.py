# Generated by Django 4.0.8 on 2023-09-13 05:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventories', '0065_auto_20230912_1651'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='increamental_id',
            field=models.IntegerField(default=0, verbose_name='increamental id'),
        ),
        migrations.AddField(
            model_name='stockadjustment',
            name='increamental_id',
            field=models.IntegerField(default=0, verbose_name='increamental id'),
        ),
        migrations.CreateModel(
            name='StockAdjustmentCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_no', models.BigIntegerField(default=0, unique=True, verbose_name='reg no')),
                ('increamental_id', models.IntegerField(default=0, verbose_name='increamental id')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PurchaseOrderCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_no', models.BigIntegerField(default=0, unique=True, verbose_name='reg no')),
                ('increamental_id', models.IntegerField(default=0, verbose_name='increamental id')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InventoryCountCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_no', models.BigIntegerField(default=0, unique=True, verbose_name='reg no')),
                ('increamental_id', models.IntegerField(default=0, verbose_name='increamental id')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
