# Generated by Django 3.2 on 2021-09-25 05:59

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0027_auto_20210925_0559'),
        ('profiles', '0015_rename_loyaltysettings_loyaltysetting'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerDebtCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('debt', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='debt')),
                ('reg_no', models.BigIntegerField(unique=True, verbose_name='reg no')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='profiles.customer')),
                ('receipt', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.receipt')),
            ],
        ),
        migrations.CreateModel(
            name='CustomerDebt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('debt', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='debt')),
                ('reg_no', models.BigIntegerField(unique=True, verbose_name='reg no')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.customer')),
                ('receipt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='sales.receipt')),
            ],
        ),
    ]
