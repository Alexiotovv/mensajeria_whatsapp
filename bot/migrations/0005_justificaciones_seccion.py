# Generated by Django 5.0 on 2025-03-22 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_justificaciones_grado'),
    ]

    operations = [
        migrations.AddField(
            model_name='justificaciones',
            name='seccion',
            field=models.CharField(default='', max_length=2),
        ),
    ]
