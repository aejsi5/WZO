# Generated by Django 3.1.7 on 2021-04-04 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WZO_App', '0002_auto_20210404_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='eort',
            name='region',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='Leitregion'),
        ),
    ]