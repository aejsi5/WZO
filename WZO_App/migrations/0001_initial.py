# Generated by Django 3.1.7 on 2021-04-04 16:56

import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Eort',
            fields=[
                ('eort_id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=10, verbose_name='Latitude')),
                ('lng', models.DecimalField(decimal_places=6, max_digits=10, verbose_name='Longditude')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Name')),
                ('street', models.CharField(blank=True, max_length=255, null=True, verbose_name='Strasse')),
                ('zip_code', models.CharField(blank=True, max_length=5, null=True, verbose_name='PLZ')),
                ('city', models.CharField(blank=True, max_length=255, null=True, verbose_name='Stadt')),
            ],
        ),
        migrations.CreateModel(
            name='WZO_User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('veh_id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('ikz', models.CharField(max_length=255, verbose_name='IKZ')),
                ('objno', models.CharField(max_length=255, verbose_name='ObjNr')),
                ('make', models.CharField(max_length=255, verbose_name='Hersteller')),
                ('model', models.CharField(max_length=255, verbose_name='Modell')),
                ('reg_date', models.DateField(verbose_name='EZ')),
                ('age', models.IntegerField(verbose_name='Alter_Tage')),
                ('service_contract', models.BooleanField(default=False, verbose_name='Servicevertrag')),
                ('eort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WZO_App.eort')),
            ],
        ),
    ]