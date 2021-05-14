# Generated by Django 3.1.7 on 2021-05-02 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WZO_App', '0022_rulewt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rulewt',
            name='age_operator',
            field=models.SmallIntegerField(blank=True, choices=[(1, '='), (2, '<'), (3, '>')], null=True, verbose_name='Fz-Alter-Operand'),
        ),
        migrations.AlterField(
            model_name='rulewt',
            name='service_contract',
            field=models.SmallIntegerField(blank=True, choices=[(1, None), (2, 'Mit Servicevertrag'), (3, 'Ohne Servicevertrag')], null=True, verbose_name='Servicevertrag'),
        ),
    ]
