from celery import shared_task
from time import sleep
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token, account_reset_token
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.conf import settings

@shared_task
def wait():
    sleep(10)
    return "DONE"

@shared_task
def send_verification_mail(domain, user):
    sleep(20)
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
