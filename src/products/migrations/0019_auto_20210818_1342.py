# Generated by Django 3.2 on 2021-08-18 13:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_auto_20210818_1205'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productvariant',
            name='product_variant_option',
        ),
        migrations.AddField(
            model_name='productvariant',
            name='product_variant',
            field=models.OneToOneField(default=0, on_delete=django.db.models.deletion.CASCADE, to='products.product'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productvariantoptionchoice',
            name='product_variant_option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productvariantoption'),
        ),
    ]
