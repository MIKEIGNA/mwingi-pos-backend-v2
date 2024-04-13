# Generated by Django 3.2 on 2021-08-10 04:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('inventories', '0013_auto_20210810_0450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stocklevel',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product'),
        ),
        migrations.DeleteModel(
            name='Product',
        ),
        migrations.DeleteModel(
            name='ProductBundle',
        ),
        migrations.DeleteModel(
            name='ProductCount',
        ),
        migrations.DeleteModel(
            name='Receipt',
        ),
        migrations.DeleteModel(
            name='ReceiptCount',
        ),
        migrations.DeleteModel(
            name='ReceiptLine',
        ),
        migrations.DeleteModel(
            name='ReceiptLineCount',
        ),
    ]
