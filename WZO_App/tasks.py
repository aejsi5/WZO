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
from celery.utils.log import get_task_logger
log = get_task_logger(__name__)

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
    print(fileid)
    csvf = Upload.objects.get(pk=fileid)
    print(csvf.record.path)
    with open(csvf.record.path, 'r', encoding='utf-8') as f:
        #csvf = io.StringIO(csvfile.read().decode('utf-8'))
        content = []
        line = 0
        reader = csv.DictReader(f,fieldnames=('osm_id', 'ort', 'plz', 'bundesland'),delimiter=';')
        for row in reader:
            if not line == 0:
                content.append(dict(row))
            line += 1
        if len(content) > 0 :
            Zip_Code.objects.all().delete()
            for i in content:
                try:
                    new = Zip_Code.objects.create(zip_code= i['plz'], city=i['ort'], state=i['bundesland'])
                    new.save()
                except Exception as e:
                    print("Zip_Code Importer")
                    print(i)
                    print(e)
    csvf.finished = True
    csvf.save()
    Zip_Code.objects.all().delete()
    return
