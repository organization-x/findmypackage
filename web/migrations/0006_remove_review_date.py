# Generated by Django 4.0.3 on 2022-11-08 23:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0005_merge_20221108_2317'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='date',
        ),
    ]
