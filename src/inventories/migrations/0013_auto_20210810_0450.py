# Generated by Django 3.2 on 2021-08-10 04:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventories', '0012_auto_20210805_1003'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='bundle',
        ),
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
        migrations.RemoveField(
            model_name='product',
            name='profile',
        ),
        migrations.RemoveField(
            model_name='product',
            name='stores',
        ),
        migrations.RemoveField(
            model_name='product',
            name='tax',
        ),
        migrations.RemoveField(
            model_name='productbundle',
            name='product_bundle',
        ),
        migrations.RemoveField(
            model_name='productcount',
            name='category',
        ),
        migrations.RemoveField(
            model_name='productcount',
            name='profile',
        ),
        migrations.RemoveField(
            model_name='productcount',
            name='tax',
        ),
        migrations.RemoveField(
            model_name='receipt',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='receipt',
            name='discount',
        ),
        migrations.RemoveField(
            model_name='receipt',
            name='store',
        ),
        migrations.RemoveField(
            model_name='receipt',
            name='user',
        ),
        migrations.RemoveField(
            model_name='receiptcount',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='receiptcount',
            name='store',
        ),
        migrations.RemoveField(
            model_name='receiptcount',
            name='user',
        ),
        migrations.RemoveField(
            model_name='receiptline',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='receiptline',
            name='product',
        ),
        migrations.RemoveField(
            model_name='receiptline',
            name='receipt',
        ),
        migrations.RemoveField(
            model_name='receiptline',
            name='store',
        ),
        migrations.RemoveField(
            model_name='receiptline',
            name='user',
        ),
        migrations.RemoveField(
            model_name='receiptlinecount',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='receiptlinecount',
            name='product',
        ),
        migrations.RemoveField(
            model_name='receiptlinecount',
            name='store',
        ),
        migrations.RemoveField(
            model_name='receiptlinecount',
            name='user',
        ),
    ]