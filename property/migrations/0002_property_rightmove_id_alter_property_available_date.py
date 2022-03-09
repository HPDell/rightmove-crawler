# Generated by Django 4.0.3 on 2022-03-09 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('property', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='rightmove_id',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='property',
            name='available_date',
            field=models.DateField(blank=True),
        ),
    ]