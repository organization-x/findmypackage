# Generated by Django 4.0.3 on 2022-10-16 23:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='review',
            old_name='stars_amount',
            new_name='stars',
        ),
    ]