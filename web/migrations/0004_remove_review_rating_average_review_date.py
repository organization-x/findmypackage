# Generated by Django 4.0.3 on 2022-10-29 01:19

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_alter_review_rating_average'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='rating_average',
        ),
        migrations.AddField(
            model_name='review',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]