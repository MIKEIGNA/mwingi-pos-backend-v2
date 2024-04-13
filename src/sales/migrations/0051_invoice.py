# Generated by Django 3.2 on 2022-02-21 09:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stores', '0037_alter_storeshift_all_refunds_during_shift'),
        ('profiles', '0040_delete_storepaymentmethod'),
        ('sales', '0050_auto_20220202_1253'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_info', models.JSONField(default=dict, verbose_name='customer_info')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='total amount')),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='discount amount')),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='tax amount')),
                ('payment_completed', models.BooleanField(default=False, verbose_name='payment completed')),
                ('item_count', models.IntegerField(default=0, verbose_name='item count')),
                ('reg_no', models.BigIntegerField(editable=False, unique=True, verbose_name='reg no')),
                ('created_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='created date')),
                ('paid_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='paid date')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='profiles.customer')),
                ('receipts', models.ManyToManyField(to='sales.Receipt')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stores.store')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
