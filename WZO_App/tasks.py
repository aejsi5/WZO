from celery import shared_task
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token, account_reset_token
from .models import *
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.conf import settings

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
def send_delete_mail(userpk):
    user = WZO_User.objects.get(pk=userpk)
    subject = "Arugula - Dein Account wurde gelöscht"
    message = render_to_string('registration/email_deleted.html', {
            'user': user.first_name,
        })
    email = EmailMessage(
                    subject, message, to=[user.email]
        )
    email.send()
    return 
