# Generated by Django 3.1.7 on 2021-04-10 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WZO_App', '0012_eort_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='deleted',
            field=models.BooleanField(default=False, verbose_name='Gelöscht'),
        ),
        migrations.AlterField(
            model_name='eort',
            name='fm_eort_id',
            field=models.CharField(max_length=255, unique=True, verbose_name='FM-Eort-ID'),
        ),
    ]
