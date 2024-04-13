# Generated by Django 3.2 on 2022-02-02 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0039_remove_storepaymentmethod_profile'),
        ('stores', '0033_alter_shiftcash_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='StorePaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.IntegerField(choices=[(0, 'Cash'), (1, 'Mpesa'), (2, 'Card'), (3, 'Points'), (4, 'Debt'), (5, 'Others')], default=0, verbose_name='payment type')),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('reg_no', models.BigIntegerField(default=0, unique=True, verbose_name='reg no')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.profile')),
            ],
        ),
    ]
