# Generated by Django 4.1.2 on 2022-10-28 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='rating_average',
            field=models.SmallIntegerField(default=0),
        ),
    ]