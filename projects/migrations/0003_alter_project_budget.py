# Generated by Django 5.0.2 on 2025-06-05 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_remove_project_image_project_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='Budget alloué'),
        ),
    ]
