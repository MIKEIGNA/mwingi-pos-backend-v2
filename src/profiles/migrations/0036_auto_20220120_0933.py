# Generated by Django 3.2 on 2022-01-20 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0035_auto_20220120_0749'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='receiptsetting',
            name='footer',
        ),
        migrations.RemoveField(
            model_name='receiptsetting',
            name='header',
        ),
        migrations.RemoveField(
            model_name='receiptsetting',
            name='image',
        ),
        migrations.RemoveField(
            model_name='receiptsetting',
            name='old_image',
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='footer1',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='footer1'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='footer2',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='footer2'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='footer3',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='footer3'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='footer4',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='footer4'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='footer5',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='footer5'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='footer6',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='footer6'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='header1',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='header1'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='header2',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='header2'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='header3',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='header3'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='header4',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='header4'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='header5',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='header5'),
        ),
        migrations.AddField(
            model_name='receiptsetting',
            name='header6',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='header6'),
        ),
    ]
