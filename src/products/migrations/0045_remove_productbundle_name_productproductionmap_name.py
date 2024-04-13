# Generated by Django 4.0.8 on 2023-09-15 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0044_productbundle_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productbundle',
            name='name',
        ),
        migrations.AddField(
            model_name='productproductionmap',
            name='name',
            field=models.CharField(default='', max_length=100, verbose_name='name'),
            preserve_default=False,
        ),
    ]
