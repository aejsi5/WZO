from django.shortcuts import render, redirect
from celery import states
from django_celery_results.models import TaskResult
from django.views import View
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.contrib.auth.forms import ValidationError as PasswordValidationError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import logout, login, authenticate, update_session_auth_hash
from django.core.mail import EmailMessage
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework import viewsets, mixins, generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import *

from .models import *
from .serializer import *
from .rules import *
from .tokens import account_activation_token, account_reset_token
from .forms import *
from .tasks import *
import logging
import json
import io
import csv
import googlemaps
gmaps = googlemaps.Client(key=settings.WZO_OPTIONS['GOOGLE_TOKEN'])
log = logging.getLogger(__name__)

# Create your views here.


###Nächste Schritte:
# RuleEngineWT muss kontrolliert werden ob es funktioniert - Check!
# Rules via Rest Schnittstelle paginiert zur Verfügung stellen -Check!
# In Tabelle in Frontend füllen - Check!

def logout_view(request):
    logout(request)
    response = redirect('/')
    return response    

class Login(View):
    template_name = "registration/login.html"

    def get(self, request):
        form = LoginForm
        return render(request,self.template_name, context={"login_form":form})

    def post(self, request):
        form =LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username,password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
        return render (request, self.template_name, context={"login_form":form, 'error': True})

class Registration(View):
    template_name = "registration/register.html"

    def get(self, request):
        form = NewUserForm
        return render(request,self.template_name, context={"register_form":form})
    
    def post(self, request):
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            current_site = get_current_site(request)
            send_verification_mail.delay(current_site.domain, request.user.pk)
            #self.send_verification_mail.(request,user.email)
            return redirect("/")
        return render (request, self.template_name, context={"register_form":form})
    
    #DEPRECIATED
    def send_verification_mail(self, request, to):
        subject = "Arugula - Bitte bestätige deine Email-Adresse"
        current_site = get_current_site(request)
        message = render_to_string('registration/email_verification.html', {
                'user': request.user.first_name,
                'protocol': settings.DEFAULT_PROTOCOL,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(request.user.pk)),
                'token':account_activation_token.make_token(request.user),
            })
        email = EmailMessage(
                        subject, message, to=[to]
            )
        email.send()
        return 

class Reset(View):
    template_name = "registration/reset.html"

    def get(self, request):
        form = ResetForm
        return render(request,self.template_name, context={"reset":form})

    def post(self, request):
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = WZO_User.objects.get(email=email)
                current_site = get_current_site(request)
                send_reset_mail.delay(current_site.domain, user.pk)
                #self.send_reset_mail(request,user)
            except:
                pass
        return render (request, self.template_name, context={"reset":form, "submit": True})

    #DEPRECIATED
    def send_reset_mail(self, request, touser):
        subject = "Arugula - Passwort Zurücksetzen"
        current_site = get_current_site(request)
        message = render_to_string('registration/email_reset.html', {
                'user': touser.first_name,
                'protocol': settings.DEFAULT_PROTOCOL,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(touser.pk)),
                'token':account_reset_token.make_token(touser),
            })
        email = EmailMessage(
                        subject, message, to=[touser.email]
            )
        email.send()
        return

class PasswordReset(View):
    template_name = "registration/reset-pw.html"

    def get(self, request, uidb64, token):
        user = self.check_token(uidb64,token)
        if user is not None:
            form = NewPasswordForm(data={'email':user.email})
            return render(request,self.template_name, context={"reset":form})
        else:
            return HttpResponse('Resettoken is invalid!')

    def post(self, request, uidb64, token):
        ruser = request.user
        user = self.check_token(uidb64,token)
        nextpage = request.GET.get('next', '/')
        if user is not None:
            form = NewPasswordForm(data={'email':user.email, 'password1': request.POST.get('password1'), 'password2': request.POST.get('password2')})
            if not form.is_valid():
                form = NewPasswordForm(data={'email':user.email})
                return render(request,self.template_name, context={"reset":form})
            if not form.cleaned_data['password1'] == form.cleaned_data['password2']:
                form = NewPasswordForm(data={'email':user.email, 'password1': request.POST.get('password1'), 'password2': request.POST.get('password2')})
                form.add_error('password1', 'Passwörter stimmen nicht überein')
                form.add_error('password2', 'Passwörter stimmen nicht überein')
                return render(request,self.template_name, context={"reset":form})
            try:
                validate_password(password=form.cleaned_data['password1'],user=user)
            except PasswordValidationError as e:
                form.add_error('password1',e)
                return render(request,self.template_name, context={"reset":form})
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            return redirect(nextpage)
        else:
            return HttpResponse('Resettoken is invalid!')

    def check_token(self, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = WZO_User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, WZO_User.DoesNotExist):
            user = None
        if user is not None and account_reset_token.check_token(user, token):
            return user
        else:
            return None

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = WZO_User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, WZO_User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('/login')
    else:
        return HttpResponse('Activation link is invalid!')

@login_required(login_url='/login/')
def welcome_view(request):
    return render(request, 'welcome.html', context={'user':request.user})

@login_required(login_url='/login/')
def index(request):
    needed_perms = ['WZO_App.view_eort','WZO_App.view_vehicle', 'WZO_App.view_workshop', 'WZO_App.view_allocation']
    for i in needed_perms:
        if request.user.has_perm(i):
            continue
        else:
            return redirect('/welcome')
    return render(request, 'index.html')

@login_required()
def run_Rules(request, ruletype):
    needed_perms = ['WZO_App.add_allocation','WZO_App.change_allocation', 'WZO_App.delete_allocation']
    for i in needed_perms:
        if request.user.has_perm(i):
            continue
        else:
            return HttpResponse(status=403)
    if ruletype == 'wear-and-tear':
        #myRules = RuleEngine('V', '20210417_143057')
        myRules = RuleEngineWT()
        myRules.run_rules()
    return redirect('/')

class Settings(View):
    template_name='settings.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            form = ProfileForm(instance=request.user)
            reset_link = self.get_password_reset_link(request)
            change_user = request.GET.get('user', None)
            change_user_action = request.GET.get('action', None)
            if change_user is not None and change_user_action is not None:
                if change_user_action == 'activate':
                    WZOUser_Api().activate(request,change_user)
                elif change_user_action == 'deactivate':
                    WZOUser_Api().deactivate(request,change_user)
                elif change_user_action == 'delete':
                    WZOUser_Api().delete(request,change_user)
        else:
            return HttpResponse(status=403)
        if request.user.has_perm('WZO_App.change_wzo_user'):
            active_user = WZO_User.objects.filter(groups__name__in=['RIV-Manager'],is_staff=False,is_superuser=False, is_active=True).exclude(groups__name__in=['RIV-Admin', 'Developer'])
            new_user = WZO_User.objects.filter(is_staff=False,is_superuser=False, is_active=True).exclude(groups__name__in=['RIV-Admin', 'Developer', 'RIV-Manager'], pk__in=active_user)
        else:
            active_user = None
            new_user = None
        return render(request, self.template_name, context={'profile_form':form, 'active_user':active_user, 'new_user':new_user, 'reset_link': reset_link})

    def post(self, request):
        if request.user.is_authenticated:
            form =ProfileForm(request.POST)
        else:
            return HttpResponse(status=403)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
        return self.get(request)

    def get_password_reset_link(self,request):
        current_site = get_current_site(request)
        protocol = settings.DEFAULT_PROTOCOL
        domain = current_site.domain
        uid = urlsafe_base64_encode(force_bytes(request.user.pk))
        token = account_reset_token.make_token(request.user)
        return "{}://{}/reset/password/{}/{}/?next={}".format(protocol,domain,uid,token,request.path)

class Calculate(View):
    template_name = "calculate.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return render(request, self.template_name)
        else:
            return HttpResponse(status=403)

class Export(View):
    template_name = "export.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.GET.get('download') == 'eorte':
                res = self.export_eorte()
                return res
            if request.GET.get('download') == 'werkstätten':
                res = self.export_workshops()
                return res
            return render(request, self.template_name)
        else:
            return HttpResponse(status=403)
    
    def export_eorte(self, *args, **kwargs):
        eorte = Eort.objects.filter(deleted=False)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="eorte_export.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(['EortID', 'FM-EortID', 'Lat', 'Lng', 'Name', 'Straße', 'Leitregion', 'PLZ'])
        for i in eorte:
            writer.writerow([i.eort_id, i.fm_eort_id, i.lat, i.lng, i.name, i.street, i.region, i.zip_code])
        return response
    
    def export_workshops(self, *args, **kwargs):
        wst = Workshop.objects.filter(deleted=False)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="werkstatt_export.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow(['WerkstattID', 'Kuerzel', 'Name', 'Straße', 'Plz', 'Telefon', 'Email-Zentrale', 'Email-Asp', 'WP-User'])
        for i in wst:
            writer.writerow([i.w_id, i.kuerzel, i.name, i.street, i.zip_code, i.phone, i.central_email, i.contact_email, i.wp_user])
        return response

class Import(View):
    template_name = "import.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            running_tasks = TaskResult.objects.filter(task_name__in=['WZO_App.tasks.import_zip_codes', 'WZO_App.tasks.import_eort', 'WZO_App.tasks.import_workshops', 'WZO_App.tasks.import_veh', 'WZO_App.tasks.import_rules']).values('task_id', 'task_name', 'status')
            if not running_tasks:
                return render(request, self.template_name)
            else:
                log.info({'tasks': running_tasks})
                return render(request, self.template_name, {'tasks': running_tasks})
        else:
            return HttpResponse(status=403)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(status=403)
        if 'import_eort' in request.FILES:
            csv_file = request.FILES['import_eort']
            ext = request.FILES['import_eort'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            upload = Upload.objects.create(pattern="EortImport", record=csv_file)
            task = import_eort.delay(upload.pk)
        elif 'import_veh' in request.FILES:
            csv_file = request.FILES['import_veh']
            ext = request.FILES['import_veh'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            upload = Upload.objects.create(pattern="VehImport", record=csv_file)
            task = import_veh.delay(upload.pk)
        elif 'import_zips' in request.FILES:
            csv_file = request.FILES['import_zips']
            ext = request.FILES['import_zips'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            upload = Upload.objects.create(pattern="ZipImport", record=csv_file)
            task = import_zip_codes.delay(upload.pk)
        elif 'import_ws' in request.FILES:
            csv_file = request.FILES['import_ws']
            ext = request.FILES['import_ws'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            upload = Upload.objects.create(pattern="WorkshopImport", record=csv_file)
            task = import_workshops.delay(upload.pk)
        elif 'import_rules' in request.FILES:
            csv_file = request.FILES['import_rules']
            ext = request.FILES['import_rules'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            upload = Upload.objects.create(pattern="WTRulesImport", record=csv_file)
            task = import_rules.delay(upload.pk)
        return render(request, self.template_name)

class HealthCheck(View):
    template_name = "healthcheck.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            services = {'Google':True}
            try:
                geocode_result = gmaps.geocode("Helmholtzstrasse 3 30165 Hannover Deutschland")
            except:
                services['Google'] = False
            return render(request, self.template_name, context=services)
        else:
            return HttpResponse(status=403)

class Eort_Api(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            eort = Eort.objects.get(fm_eort_id=pk)
        except Eort.DoesNotExist:
            try:
                eort = Eort.objects.get(eort_id=pk)
            except:
                return HttpResponse(status=404)
        serializer = Eort_Serializer(eort, many=False)
        res = {
            'data': serializer.data
        }
        return Response(res)
 
class EortVehicleList_Api(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            eort = Eort.objects.get(fm_eort_id=pk)
        except Eort.DoesNotExist:
            try:
                eort = Eort.objects.get(eort_id=pk)
            except:
                return HttpResponse(status=404)
        vehicles = Vehicle.objects.filter(eort=eort, deleted=False)
        serializer = Veh_Serializer(vehicles, many=True)
        res = {
            'data': serializer.data
        }
        return Response(res)

class Eort_List_Api(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        #try
        vehs = None
        eorte = None
        eq = self.eort_query(request.GET)
        vq = self.veh_query(request.GET)
        if vq:
            vehs = Vehicle.objects.filter(vq)
        if eq:
            eorte = Eort.objects.filter(eq)
        if vehs is not None and eorte is not None:
            selected = Eort.objects.filter(eort_id__in=vehs.values('eort')).filter(eort_id__in=eorte.values('eort_id')).filter(displayable=True)
        elif vehs is not None and eorte is None:
            selected = Eort.objects.filter(eort_id__in=vehs.values('eort')).filter(displayable=True)
        elif vehs is None and eorte is not None:
            selected = Eort.objects.filter(eort_id__in=eorte.values('eort_id')).filter(displayable=True)
        else:
            selected = Eort.objects.filter(displayable=True)
        #except Eort.DoesNotExist:
        #    return HttpResponse(status=404)
        serializer = Eort_Serializer(selected, many=True)
        res = {
            'data': serializer.data
        }
        return Response(res)

    def eort_query(self, params):
        if not params:
            return None
        query = Q()
        query.connector = Q.AND
        is_relevant = False
        for key in params:
            if key in ['lat', 'lng', 'name', 'street', 'zip_code', 'city', 'region']:
                is_relevant = True
                val = params.get(key, None).split(',')
                log.debug('Eort Query: Eort Param {}',format(key))
                log.debug(val)
                query.add(self.or_operator(key, val),Q.AND)
        if is_relevant:
            return query 
        else:
            return None

    def veh_query(self, params):
        if not params:
            return None
        query = Q()
        query.connector = Q.AND
        is_relevant = False
        for key in params:
            if key in ['ikz', 'objno', 'make', 'model', 'reg_date', 'age', 'service_contract']:
                is_relevant = True
                val = params.get(key, None).split(',')
                log.debug('Eort Query: Vehicle Param {}',format(key))
                log.debug(val)
                query.add(self.or_operator(key, val),Q.AND)
        if is_relevant:
            return query 
        else:
            return None                  
                
    def or_operator(self, key, qlist):
        if qlist:
            result = Q()
            result.connector = Q.OR
            for i in qlist:
                if i == '':
                    continue
                if i[0] == '%' and i[-1] == '%':
                    result.add(Q((f'{key}__contains', i[1:-1])), Q.OR)
                elif i[0] == '%' and not i[-1] == '%':
                    result.add(Q((f'{key}__endswith', i[1:])), Q.OR)
                elif i[0:5] == 'lte__':
                    result.add(Q((f'{key}__lte', i[5:])), Q.OR)
                elif i[0:5] == 'gte__':
                    result.add(Q((f'{key}__gte', i[5:])), Q.OR)
                elif not i[0] == '%' and i[-1] == '%':
                    result.add(Q((f'{key}__startswith', i[:-1])), Q.OR)
                else:
                    result.add(Q((key, i)), Q.OR)
            return result                

class Vehicle_Api(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            v = Vehicle.objects.get(ikz=pk)
        except Vehicle.DoesNotExist:
            return HttpResponse(status=404)
        serializer = Veh_Serializer(v, many=False)
        res = {
            'data': serializer.data
        }
        return Response(res)

class VehicleWorkshopList_Api(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            v = Vehicle.objects.get(ikz=pk)
        except Vehicle.DoesNotExist:
            return HttpResponse(status=404)
        #allo = Allocation.objects.filter(v_id=v)
        #serializer = Allocation_Serializer(allo, many=True)
        serializer = VehAllo_Serializer(v, many=False)
        res = {
            'data': serializer.data['workshops']
        }
        return Response(res)

class RulesSearchpagination(PageNumberPagination):
    page_size = 100

class WTRulesList_Api(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = RulesSearchpagination
    serializer_class = RuleWT_Serializer

    def get_queryset(self):
        params = self.request.GET
        if params:
            query = self.search(params)
            if query:
                Rules = RuleWT.objects.filter(query)
                return Rules
        Rules = RuleWT.objects.all()
        return Rules

    def search(self, params):
        query = Q()
        query.connector = Q.AND
        is_relevant = False
        for key in params:
            if key in ['make', 'kuerzel', 'address', 'note']:
                is_relevant = True
                val = params.get(key, None).split(',')
                query.add(self.or_operator(key, val),Q.AND)
        if is_relevant:
            return query 
        else:
            return None

    def or_operator(self, key, qlist):
        if qlist:
            result = Q()
            result.connector = Q.OR
            for i in qlist:
                if i == '':
                    continue
                if i[0] == '%' and i[-1] == '%':
                    result.add(Q((f'{key}__contains', i[1:-1])), Q.OR)
                elif i[0] == '%' and not i[-1] == '%':
                    result.add(Q((f'{key}__endswith', i[1:])), Q.OR)
                elif not i[0] == '%' and i[-1] == '%':
                    result.add(Q((f'{key}__startswith', i[:-1])), Q.OR)
                else:
                    result.add(Q((key, i)), Q.OR)
            return result 

class WZOUser_Api(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self,request,pk, *args, **kwargs):
        if request.user.has_perm('WZO_App.delete_wzo_user'):
            user = WZO_User.objects.get(pk=pk)
            first = user.first_name
            email = user.email
            user.delete()
            send_delete_mail.delay(first, email)
            #self.send_delete_mail(user)
            return Response(status=200)
        else:
            return Response(status=403)
    
    def activate(self, request, pk, *args, **kwargs):
        if request.user.has_perm('WZO_App.change_wzo_user'):
            user = WZO_User.objects.get(pk=pk)
            group = Group.objects.get(name='RIV-Manager')
            user.groups.add(group)
            user.save()
            send_activation_mail.delay(user.pk)
            #self.send_activation_mail(user)
            return Response(status=202)
        else:
            return Response(status=403)
    
    def deactivate(self, request, pk, *args, **kwargs):
        if request.user.has_perm('WZO_App.change_wzo_user'):
            user = WZO_User.objects.get(pk=pk)
            group = Group.objects.get(name='RIV-Manager')
            user.groups.remove(group)
            user.save()
            send_deactivation_mail.delay(user.pk)
            #self.send_deactivation_mail(user)
            return Response(status=202)
        else:
            return Response(status=403)

    #DEPRECIATED
    def send_activation_mail(self, touser):
        subject = "Arugula - Du wurdest freigeschaltet"
        message = render_to_string('registration/email_activated.html', {
                'user': touser.first_name,
            })
        email = EmailMessage(
                        subject, message, to=[touser.email]
            )
        email.send()
        return 

    #DEPRECIATED
    def send_deactivation_mail(self, touser):
        subject = "Arugula - Du wurdest gesperrt"
        message = render_to_string('registration/email_deactivated.html', {
                'user': touser.first_name,
            })
        email = EmailMessage(
                        subject, message, to=[touser.email]
            )
        email.send()
        return 
    
    #DEPRECIATED
    def send_delete_mail(self, touser):
        subject = "Arugula - Dein Account wurde gelöscht"
        message = render_to_string('registration/email_deleted.html', {
                'user': touser.first_name,
            })
        email = EmailMessage(
                        subject, message, to=[touser.email]
            )
        email.send()
        return                
    



