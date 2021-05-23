from django.db import models
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage

# Create your models here.
class WZO_User(AbstractUser):
    pass

class Zip_Code(models.Model):
    zip_id = models.AutoField('ID', primary_key=True)
    zip_code = models.CharField('PLZ', max_length=5, null=False, blank=False)
    city = models.CharField('Stadt', max_length=255, null=False, blank=False)
    state = models.CharField('Bundesland', max_length=255, null=False, blank=False)

    def __str__(self):
        return str(self.zip_code)

    class Meta:
        app_label = "WZO_App"

class Eort(models.Model):
    eort_id = models.AutoField('ID', primary_key=True)
    fm_eort_id = models.CharField('FM-Eort-ID', max_length=255, null=False, blank=False, unique=True)
    lat = models.DecimalField('Latitude',decimal_places=6, max_digits=10, null=True, blank=True)
    lng = models.DecimalField('Longditude',decimal_places=6, max_digits=10, null=True, blank=True)
    name = models.CharField('Name', max_length=255, null=True, blank=True)
    street = models.CharField('Strasse', max_length=255, null=True, blank=True)
    region = models.CharField('Leitregion', max_length=2, null=True, blank=True)
    zip_code = models.CharField('PLZ', max_length=5, null=True, blank=True)
    city = models.ForeignKey(Zip_Code,on_delete=models.CASCADE,null=True, blank=True)
    deleted = models.BooleanField('Gelöscht', default=False)
    displayable = models.BooleanField('Anzeigbar', default=False)

    def __str__(self):
        return str(self.eort_id)

    def save(self, *args, **kwargs):
        if self.lat is not None and self.lng is not None:
            self.displayable = True
        # Now we call the actual save method
        super(Eort, self).save(*args, **kwargs)

    class Meta:
        app_label = "WZO_App"

class Workshop(models.Model):
    w_id = models.AutoField('ID', primary_key=True)
    kuerzel = models.CharField('Kürzel', max_length=7, null=False, blank=False, unique=True)
    name = models.CharField('Name', max_length=255, null=False, blank=False)
    street = models.CharField('Straße', max_length=255, null=True, blank=True)
    zip_code = models.CharField('PLZ', max_length=5, null=True, blank=True)
    city = models.ForeignKey(Zip_Code,on_delete=models.CASCADE,null=True, blank=True)
    phone = models.CharField('Telefon', max_length=255, null=True, blank=True)
    central_email = models.CharField('Zentral-Email', max_length=255, null=True, blank=True)
    contact_email = models.CharField('Asp-Email', max_length=255, null=True, blank=True)
    wp_user = models.BooleanField('WP-User', default=False)
    deleted = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.kuerzel)

    class Meta:
        app_label = "WZO_App"


class Vehicle(models.Model):
    veh_id = models.AutoField('ID', primary_key=True)
    eort = models.ForeignKey(Eort, on_delete=models.CASCADE)
    ikz = models.CharField('IKZ', max_length=255, null=False, blank=False, unique=True)
    objgroup = models.CharField('Objektgruppe', max_length=255, null=False, blank=False)
    objno = models.CharField('ObjNr', max_length=255, null=False, blank=False)
    make = models.CharField('Hersteller', max_length=255, null=False, blank=False)
    model = models.CharField('Modell', max_length=255, null=False, blank=False)
    year = models.CharField('Baujahr', max_length=255, null=False, blank=False)
    reg_date = models.DateField('EZ', null=False, blank=False)
    age = models.IntegerField('Alter_Tage', null=False, blank=False)
    service_contract= models.BooleanField('Servicevertrag', default=False, null=False, blank=False)
    deleted = models.BooleanField('Gelöscht', default=False)

    def __str__(self):
        return str(self.ikz)

    class Meta:
        app_label = "WZO_App"

class RuleWT(models.Model):
    rule_id = models.AutoField('ID', primary_key=True)
    row = models.IntegerField('Zeile', blank=True, null=True)
    lat = models.FloatField('Lat', blank=True, null=True)
    lng = models.FloatField('Lng', blank=True, null=True)
    radius = models.FloatField('Radius', blank=True, null=True)
    lbr = models.BooleanField('LocationBasedRule', default=False)
    zip_code = models.CharField('PLZ',max_length=255, null=True, blank=True)
    make = models.CharField('Hersteller',max_length=255, null=True, blank=True)
    model = models.CharField('Fz-Typ',max_length=255, null=True, blank=True)
    objno = models.CharField('Fz-ObjNr',max_length=255, null=True, blank=True)
    year = models.CharField('Baujahr',max_length=255, null=True, blank=True)
    age = models.CharField('Fz-Alter',max_length=255,null=True, blank=True)
    service_contract = models.CharField('Service-Vertrag',max_length=255,null=True, blank=True)
    ikz = models.CharField('IKZ', max_length=255, null=True, blank=True)
    kuerzel = models.CharField('Werkstatt-Kürzel', max_length=20, null=False, blank=False)
    address = models.CharField('Adresse',max_length=255, null=True, blank=True)
    note = models.CharField('Bemerkung',max_length=255, null=True, blank=True)

    def update_row_numbers(self, *args, **kwargs):
        rules = RuleWT.objects.all()
        j = 1
        for i in rules:
            i.row = j 
            j += 1
            i.save()

    def save(self, *args, **kwargs):
        if self.lat and self.lng:
            self.lbr = True
        else:
            self.lbr = False
        super(RuleWT, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.row)

    class Meta:
        app_label = "WZO_App"

class Allocation(models.Model):
    ALLO_OPTIONS = (
        ('V', 'Verschleiß'),
        ('U', 'Unfall'),
        ('RD', 'Reifendienstleister'),
        ('RP', 'Reifenpartner'),
        ('G', 'Glasbruch')
    )
    a_id = models.AutoField('ID', primary_key=True)
    a_type = models.CharField('Art', max_length=2, choices=ALLO_OPTIONS) 
    v_id = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=False, blank=False)
    w_id =  models.ForeignKey(Workshop, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return str(self.a_id)

    class Meta:
        app_label = "WZO_App"
        unique_together = ('a_type', 'v_id')

fs = FileSystemStorage(location=os.path.join(BASE_DIR, 'WZO_App', 'media','uploads'))

class Upload(models.Model):
    upload_id = models.AutoField('ID', primary_key=True)
    pattern = models.CharField('Datei-Typ',max_length=255, null=False, blank=False)
    inserted = models.DateTimeField('Angelegt',auto_now_add=True, null=False, blank=False)
    record = models.FileField(storage=fs)
    finished = models.BooleanField('Fertig', default=False)

    def __str__(self):
        return str(self.upload_id)

    class Meta:
        app_label = "WZO_App"




