# Generated by Django 3.2 on 2021-10-21 11:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0030_auto_20211019_1519'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaseorderline',
            name='cost',
        ),
        migrations.RemoveField(
            model_name='purchaseorderline',
            name='counted_stock',
        ),
        migrations.RemoveField(
            model_name='purchaseorderline',
            name='difference',
        ),
        migrations.RemoveField(
            model_name='purchaseorderline',
            name='expected_stock',
        ),
        migrations.RemoveField(
            model_name='purchaseorderline',
            name='inventory_count',
        ),
        migrations.AddField(
            model_name='purchaseorderline',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='amount'),
        ),
        migrations.AddField(
            model_name='purchaseorderline',
            name='purchase_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='purchase cost'),
        ),
        migrations.AddField(
            model_name='purchaseorderline',
            name='purchase_order',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='inventories.purchaseorder'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorderline',
            name='quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='quantity'),
        ),
        migrations.CreateModel(
            name='PurchaseOrderAdditionalCost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='amount')),
                ('purchase_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventories.purchaseorder')),
            ],
        ),
    ]
