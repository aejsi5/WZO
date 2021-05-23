from celery import shared_task
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token, account_reset_token
from .models import *
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.conf import settings
import csv
import logging
import googlemaps
import datetime
gmaps = googlemaps.Client(key=settings.WZO_OPTIONS['GOOGLE_TOKEN'])
log = logging.getLogger(__name__)


@shared_task
def send_verification_mail(domain, userpk):
    user = WZO_User.objects.get(pk=userpk)
    subject = "Arugula - Bitte bestätige deine Email-Adresse"
    message = render_to_string('registration/email_verification.html', {
            'user': user.first_name,
            'protocol': settings.DEFAULT_PROTOCOL,
            'domain': domain,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':account_activation_token.make_token(user),
        })
    email = EmailMessage(
                    subject, message, to=[user.email]
        )
    email.send()
    return 

@shared_task
def send_reset_mail(domain, userpk):
    user = WZO_User.objects.get(pk=userpk)
    subject = "Arugula - Passwort Zurücksetzen"
    message = render_to_string('registration/email_reset.html', {
            'user': user.first_name,
            'protocol': settings.DEFAULT_PROTOCOL,
            'domain': domain,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':account_reset_token.make_token(user),
        })
    email = EmailMessage(
                    subject, message, to=[user.email]
        )
    email.send()
    return

@shared_task
def send_activation_mail(userpk):
    user = WZO_User.objects.get(pk=userpk)
    subject = "Arugula - Du wurdest freigeschaltet"
    message = render_to_string('registration/email_activated.html', {
            'user': user.first_name,
        })
    email = EmailMessage(
                    subject, message, to=[user.email]
        )
    email.send()
    return 

@shared_task
def send_deactivation_mail(userpk):
    user = WZO_User.objects.get(pk=userpk)
    subject = "Arugula - Du wurdest gesperrt"
    message = render_to_string('registration/email_deactivated.html', {
            'user': user.first_name,
        })
    email = EmailMessage(
                    subject, message, to=[user.email]
        )
    email.send()
    return 

@shared_task
def send_delete_mail(user_first, user_mail):
    subject = "Arugula - Dein Account wurde gelöscht"
    message = render_to_string('registration/email_deleted.html', {
            'user': user_first,
        })
    email = EmailMessage(
                    subject, message, to=[user_mail]
        )
    email.send()
    return 

@shared_task
def import_zip_codes(fileid):
    log.info("ZipImporter started. Upload-PK: {}".format(fileid))
    csvf = Upload.objects.get(pk=fileid)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        next(f,None) #Skip Header
        reader = csv.DictReader(f,fieldnames=('osm_id', 'ort', 'plz', 'bundesland'),delimiter=';')
        Zip_Code.objects.all().delete()
        for counter, row in enumerate(reader):
            content = dict(row) 
            try:
                new = Zip_Code.objects.create(zip_code= content['plz'], city=content['ort'], state=content['bundesland'])
                new.save()
            except Exception as e:
                log.debug("Error occured")
                log.debug(content)
                log.debug(e)
                pass
            print("DONE: {}".format(counter),end="\r")
    csvf.finished = True
    csvf.save()
    log.info("Task completed")
    print("")
    print("Fertig")
    return

def get_zip_obj(zip_code):
    cobj = Zip_Code.objects.filter(zip_code=zip_code).first()
    return cobj

@shared_task
def import_workshops(fileid):
    log.info("Workshop Importer started.Upload-PK: {}".format(fileid))
    csvf = Upload.objects.get(pk=fileid)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        next(f,None) #Skip Header
        count_created = 0
        count_updated = 0
        count_error = 0
        reader = csv.DictReader(f,fieldnames=('kuerzel', 'name', 'street', 'zip_code', 'phone', 'central_email', 'contact_email', 'wp_user'),delimiter=';')
        Workshop.objects.all().update(deleted=True)
        for counter,row in enumerate(reader):
            content = dict(row) 
            c = get_zip_obj(content['zip_code'])
            try:
                new, created = Workshop.objects.update_or_create(kuerzel= content['kuerzel'], defaults={'name':content['name'], 'street':content['street'], 'zip_code':content['zip_code'], 'phone':content['phone'], 'central_email':content['central_email'], 'contact_email':content['contact_email'], 'wp_user':content['wp_user'], 'city':c})
                new.save()
                if created:
                    count_created += 1
                else:
                    count_updated += 1
            except Exception as e:
                log.debug("Error occured")
                log.debug(content)
                log.error(e)
                count_error += 1
                pass
            print("DONE: {}".format(counter),end="\r")
    Workshop.objects.filter(deleted=True).delete()
    log.info("{} Workshops created, {} Workshops updated, {} failed to update/create".format(count_created, count_updated, count_error))
    csvf.finished = True
    csvf.save()
    log.info("Task completed")
    print("")
    print("Fertig")
    return

def get_eort_by_fm_eort_id(fm_eort_id):
    try:
        obj = Eort.objects.get(fm_eort_id=fm_eort_id)
        return obj
    except:
        return None

def norm_street(street: str) -> str:
    street = street.lower()
    street = street.replace('ä', 'ae').replace('ö','oe').replace('ü', 'ue').replace('ß', 'ss')
    street = street.replace('str.', 'strasse')
    street = street.replace('  ', '')
    return street

def get_lat_lng(cityobj, street):
    if cityobj is not None:
        address = street + " " + cityobj.zip_code + " " + cityobj.state
    else:
        return {'lat': None, 'lng': None}
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        return geocode_result[0]['geometry']['location']
    else:
        return {'lat': None, 'lng': None}

def update_eort(old_obj, new_obj):
    update_geo = False
    if old_obj.street != new_obj['street'] or old_obj.zip_code != new_obj['zip_code']:
        update_geo = True
    old_obj.name = new_obj['name']
    old_obj.street = new_obj['street']
    old_obj.region = new_obj['region']
    old_obj.zip_code = new_obj['zip_code']
    old_obj.city = new_obj['city']
    old_obj.deleted = new_obj['deleted']
    if update_geo:
        geodata = get_lat_lng(new_obj['city'],new_obj['street'])
        old_obj.lat = geodata['lat']
        old_obj.lat = geodata['lng']
    old_obj.save()

def create_eort(obj):
    geodata = get_lat_lng(obj['city'],obj['street'])
    new = Eort(fm_eort_id = obj['fm_eort_id'], name = obj['name'], street = obj['street'], region = obj['region'], zip_code = obj['zip_code'], city = obj['city'], deleted = obj['deleted'], lat = geodata['lat'], lng = geodata['lng'])
    new.save()

@shared_task
def import_eort(fileid):
    log.info("Eort Importer started.Upload-PK: {}".format(fileid))
    csvf = Upload.objects.get(pk=fileid)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        next(f,None) #Skip Header
        count_created = 0
        count_updated = 0
        count_error = 0
        reader = csv.DictReader(f,fieldnames=('fm_eort_id', 'name', 'street', 'zip_code'),delimiter=';')
        Eort.objects.all().update(deleted=True)
        for counter,row in enumerate(reader):
            content = dict(row)
            try:
                c = get_zip_obj(content['zip_code'])
                obj = get_eort_by_fm_eort_id(content['fm_eort_id'])
                if obj is not None:
                    update_eort(obj, {"name":content['name'], "street":norm_street(content['street']), "zip_code": content['zip_code'], "city": c, "region": content['zip_code'][0:2], "deleted": False})
                    count_updated += 1
                    operation = "UPDATE"
                else:
                    create_eort({"fm_eort_id": content['fm_eort_id'], "name":content['name'], "street":norm_street(content['street']), "zip_code": content['zip_code'], "city": c, "region": content['zip_code'][0:2], "deleted": False})
                    count_created += 1
                    operation = "CREATE"
            except Exception as e:
                count_error += 1
                log.debug("An Error occured")
                log.debug(e)
                log.debug("Operation {} failed".format(operation))
                log.debug({"fm_eort_id": content['fm_eort_id'], "name":content['name'], "street":norm_street(content['street']), "zip_code": content['zip_code'], "city": c, "region": content['zip_code'][0:2], "deleted": False})
                pass
            print("DONE: {}".format(counter),end="\r")
    Eort.objects.filter(deleted=True).delete()
    log.info("{} Eorte created, {} Eorte updated, {} failed to update/create".format(count_created, count_updated, count_error))
    csvf.finished = True
    csvf.save()
    log.info("Task completed")
    print("")
    print("Fertig")
    return

@shared_task
def import_veh(fileid):
    log.info("Veh Importer started.Upload-PK: {}".format(fileid))
    csvf = Upload.objects.get(pk=fileid)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        next(f,None) #Skip Header
        count_created = 0
        count_updated = 0
        count_error = 0
        reader = csv.DictReader(f,fieldnames=('fm_eort_id', 'ikz', 'objno', 'objgroup', 'make', 'model', 'reg_date', 'year','service_contract'),delimiter=';')
        Vehicle.objects.all().update(deleted=True)
        for counter,row in enumerate(reader):
            content = dict(row)          
            try:
                eort = Eort.objects.get(fm_eort_id=content['fm_eort_id'])
                age = datetime.datetime.now() - datetime.datetime.strptime(content['reg_date'],'%Y-%m-%d')
                obj, created = Vehicle.objects.update_or_create(ikz=content['ikz'], defaults={"eort": eort, "objno": content['objno'], "objgroup": content['objgroup'],"make": content['make'], "model": content['model'], "reg_date": content['reg_date'], "year": content['year'],"service_contract": content['service_contract'], "age": age.days, "deleted": False})
                obj.save()
                if created:
                    count_created += 1
                else:
                    count_updated += 1
            except Exception as e:
                log.debug("An Error occured")
                log.debug(content)
                log.error(e)
                count_error += 1
                pass
            print("DONE: {}".format(counter),end="\r")
    Vehicle.objects.filter(deleted=True).delete()
    log.info("{} Vehicles created, {} Vehicles updated, {} failed to update/create".format(count_created, count_updated, count_error))
    csvf.finished = True
    csvf.save()
    log.info("Task completed")
    print("")
    print("Fertig")
    return

def to_float(obj):
    try:
        return float(obj)
    except:
        return None

def check_empty_string(obj):
    if obj == '':
        return None
    else:
        return str(obj)

@shared_task
def import_rules(fileid):
    log.info("Rule Importer started.Upload-PK: {}".format(fileid))
    csvf = Upload.objects.get(pk=fileid)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        next(f,None) #Skip Header
        reader = csv.DictReader(f,fieldnames=('lat', 'lng', 'radius', 'zip_code', 'make', 'model', 'objno', 'year', 'age', 'service_contract', 'ikz', 'kuerzel', 'address', 'note'),delimiter=';')
        RuleWT.objects.all().delete()
        for counter,row in enumerate(reader):
            rd = dict(row)
            try:
                new = RuleWT()
                new.lat = to_float(rd['lat'])
                new.lng = to_float(rd['lng'])
                new.radius = to_float(rd['radius'])
                new.zip_code = check_empty_string(rd['zip_code'])
                new.make = check_empty_string(rd['make'])
                new.model = check_empty_string(rd['model'])
                new.objno = check_empty_string(rd['objno'])
                new.year = check_empty_string(rd['year'])
                new.age = check_empty_string(rd['age'])
                new.service_contract = check_empty_string(rd['service_contract'])
                new.ikz = check_empty_string(rd['ikz'])
                new.kuerzel = check_empty_string(rd['kuerzel'])
                new.address = check_empty_string(rd['address'])
                new.note = check_empty_string(rd['note'])
                new.save()
            except Exception as e:
                log.debug("An Error occured")
                log.debug(rd)
                log.error(e)
                pass
            print("DONE: {}".format(counter),end="\r")
    print("")
    print("Update Row Index started")
    new.update_row_numbers()
    log.info("Task completed")
    print("Fertig")
    return