# Generated by Django 2.2.2 on 2019-06-17 05:24

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='statement',
            name='url',
            field=models.URLField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
