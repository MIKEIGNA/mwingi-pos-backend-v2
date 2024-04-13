# Generated by Django 3.2 on 2021-08-01 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0004_auto_20210730_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='categorycount',
            name='image_color',
            field=models.IntegerField(choices=[(0, 'Cash'), (1, 'Mpesa'), (2, 'Cheque'), (3, 'Card'), (4, 'Voucher'), (5, 'Free'), (6, 'Debt'), (100, 'Unknown')], default=0, verbose_name='image color'),
        ),
    ]