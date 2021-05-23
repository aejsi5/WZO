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
        content = []
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
    log.debug("Task completed")
    print("Fertig")
    return

def get_zip_obj(zip_code):
    cobj = Zip_Code.objects.filter(zip_code=zip_code).first()
    return cobj

@shared_task
def import_workshops(fileid):
    log.info("Workshop Importer started")
    csvf = Upload.objects.get(pk=fileid)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        next(f,None) #Skip Header
        content = []
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
                pass
            print("DONE: {}".format(counter),end="\r")
    Workshop.objects.filter(deleted=True).delete()
    log.info("{} Workshops created, {} Vehicles updated, {} failed to update/create".format(count_created, count_updated, count_error))
    csvf.finished = True
    csvf.save()
    log.debug("Task completed")
    print("Fertig")
    return
