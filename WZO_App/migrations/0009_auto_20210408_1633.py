# Generated by Django 3.1.7 on 2021-04-08 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WZO_App', '0008_auto_20210408_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eort',
            name='city',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Stadt'),
        ),
    ]