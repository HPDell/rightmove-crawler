# Generated by Django 4.0.3 on 2022-03-12 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property', '0004_alter_property_baths'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='furnished',
            field=models.BooleanField(blank=True, default=True),
            preserve_default=False,
        ),
    ]
