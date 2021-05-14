from django.shortcuts import render, redirect
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
            self.send_verification_mail(request,user.email)
            return redirect("/")
        return render (request, self.template_name, context={"register_form":form})
    
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
                self.send_reset_mail(request,user)
            except:
                pass
        return render (request, self.template_name, context={"reset":form, "submit": True})

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
        print(nextpage)
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
            active_user = WZO_User.objects.filter(groups__name__in=['RIV-Manager'],is_staff=False,is_superuser=False).exclude(groups__name__in=['RIV-Admin', 'Developer'])
            new_user = WZO_User.objects.filter(is_staff=False,is_superuser=False).exclude(groups__name__in=['RIV-Admin', 'Developer', 'RIV-Manager'], pk__in=active_user)
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
            return render(request, self.template_name)
        else:
            return HttpResponse(status=403)

class Import(View):
    template_name = "import.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return render(request, self.template_name)
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
            self.import_eort(csv_file)
        elif 'import_veh' in request.FILES:
            csv_file = request.FILES['import_veh']
            ext = request.FILES['import_veh'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            self.import_veh(csv_file)
        elif 'import_zips' in request.FILES:
            csv_file = request.FILES['import_zips']
            ext = request.FILES['import_zips'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            self.import_zip_codes(csv_file)
        elif 'import_ws' in request.FILES:
            csv_file = request.FILES['import_ws']
            ext = request.FILES['import_ws'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            self.import_workshops(csv_file)
        elif 'import_rules' in request.FILES:
            csv_file = request.FILES['import_rules']
            ext = request.FILES['import_rules'].name.split('.')[-1]
            allowed_ext = ['csv', 'CSV']
            if not ext in allowed_ext:
                ctx = {}
                ctx['error'] = 'File-Type not allowed'
                return render(request, self.template_name, ctx)
            self.import_rules(csv_file)
        return render(request, self.template_name)

    def import_eort(self, csvfile, *args, **kwargs):
        log.info("Eort Importer started")
        csvf = io.StringIO(csvfile.read().decode('utf-8'))
        content = []
        header = True
        count_created = 0
        count_updated = 0
        count_error = 0
        reader = csv.DictReader(csvf,fieldnames=('fm_eort_id', 'name', 'street', 'zip_code'),delimiter=';')
        Eort.objects.all().update(deleted=True)
        for row in reader:
            if header:
                #Skip header
                header = False
                continue
            content = dict(row)
            try:
                c = self.get_zip_obj(content['zip_code'])
                obj = self.get_eort_by_fm_eort_id(content['fm_eort_id'])
                if obj is not None:
                    self.update_eort(obj, {"name":content['name'], "street":self.norm_street(content['street']), "zip_code": content['zip_code'], "city": c, "region": content['zip_code'][0:2], "deleted": False})
                    count_updated += 1
                else:
                    self.create_eort({"fm_eort_id": content['fm_eort_id'], "name":content['name'], "street":self.norm_street(content['street']), "zip_code": content['zip_code'], "city": c, "region": content['zip_code'][0:2], "deleted": False})
                    count_created += 1
            except Exception as e:
                count_error += 1
                log.info(content)
                log.error(e)
                log.debug({"fm_eort_id": content['fm_eort_id'], "name":content['name'], "street:":self.norm_street(content['street']), "zip_code": content['zip_code'], "city": c, "region": content['zip_code'][0:2], "deleted": False})
        Eort.objects.filter(deleted=True).delete()
        log.info("{} Eorte created, {} Eorte updated, {} failed to update/create".format(count_created, count_updated, count_error))

    def get_eort_by_fm_eort_id(self, fm_eort_id):
        try:
            obj = Eort.objects.get(fm_eort_id=fm_eort_id)
            return obj
        except:
            return None

    def create_eort(self, obj):
        geodata = self.get_lat_lng(obj['city'],obj['street'])
        new = Eort(fm_eort_id = obj['fm_eort_id'], name = obj['name'], street = obj['street'], region = obj['region'], zip_code = obj['zip_code'], city = obj['city'], deleted = obj['deleted'], lat = geodata['lat'], lng = geodata['lng'])
        new.save()
    
    def update_eort(self, old_obj, new_obj):
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
            geodata = self.get_lat_lng(new_obj['city'],new_obj['street'])
            old_obj.lat = geodata['lat']
            old_obj.lat = geodata['lng']
        old_obj.save()

    def get_zip_obj(self, zip_code):
        cobj = Zip_Code.objects.filter(zip_code=zip_code).first()
        return cobj

    def get_lat_lng(self, cityobj, street):
        if cityobj is not None:
            address = street + " " + cityobj.zip_code + " " + cityobj.state
        else:
            return {'lat': None, 'lng': None}
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            return geocode_result[0]['geometry']['location']
        else:
            return {'lat': None, 'lng': None}

    def norm_street(self, street: str) -> str:
        street = street.lower()
        street = street.replace('ä', 'ae').replace('ö','oe').replace('ü', 'ue').replace('ß', 'ss')
        street = street.replace('str.', 'strasse')
        street = street.replace('  ', '')
        return street

    def import_zip_codes(self, csvfile, *args, **kwargs):
        csvf = io.StringIO(csvfile.read().decode('utf-8'))
        content = []
        line = 0
        reader = csv.DictReader(csvf,fieldnames=('osm_id', 'ort', 'plz', 'bundesland'),delimiter=';')
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
                    log.info("Zip_Code Importer")
                    log.info(i)
                    log.error(e)

    def import_veh(self, csvfile, *args, **kwargs):
        log.info("Vehicle Importer started")
        csvf = io.StringIO(csvfile.read().decode('utf-8'))
        content = []
        header = True
        count_created = 0
        count_updated = 0
        count_error = 0
        reader = csv.DictReader(csvf,fieldnames=('fm_eort_id', 'ikz', 'objno', 'objgroup', 'make', 'model', 'reg_date', 'year','service_contract'),delimiter=';')
        Vehicle.objects.all().update(deleted=True)
        for row in reader:
            if header:
                #Skip header
                header = False
                continue
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
                log.info("Veh Importer")
                log.info(content)
                log.error(e)
                count_error += 1
        Vehicle.objects.filter(deleted=True).delete()
        log.info("{} Vehicles created, {} Vehicles updated, {} failed to update/create".format(count_created, count_updated, count_error))

    def import_workshops(self, csvfile, *args, **kwargs):
        log.info("Workshop Importer started")
        csvf = io.StringIO(csvfile.read().decode('utf-8'))
        content = []
        header = True
        count_created = 0
        count_updated = 0
        count_error = 0
        reader = csv.DictReader(csvf,fieldnames=('kuerzel', 'name', 'street', 'zip_code', 'phone', 'central_email', 'contact_email', 'wp_user'),delimiter=';')
        Workshop.objects.all().update(deleted=True)
        for row in reader:
            if header:
                #Skip header
                header = False
                continue
            content = dict(row) 
            c = self.get_zip_obj(content['zip_code'])
            try:
                new, created = Workshop.objects.update_or_create(kuerzel= content['kuerzel'], defaults={'name':content['name'], 'street':content['street'], 'zip_code':content['zip_code'], 'phone':content['phone'], 'central_email':content['central_email'], 'contact_email':content['contact_email'], 'wp_user':content['wp_user'], 'city':c})
                new.save()
                if created:
                    count_created += 1
                else:
                    count_updated += 1
            except Exception as e:
                log.info("Workshop Importer")
                log.info(content)
                log.error(e)
        Workshop.objects.filter(deleted=True).delete()
        log.info("{} Workshops created, {} Vehicles updated, {} failed to update/create".format(count_created, count_updated, count_error))

    def import_rules(self, csvfile, *args, **kwargs):
        log.info("Rule Importer started")
        RuleWT.objects.all().delete()
        csvf = io.StringIO(csvfile.read().decode('utf-8'))
        content = []
        line = 0
        #myRules = RuleBuilder('V')
        reader = csv.DictReader(csvf,fieldnames=('lat', 'lng', 'radius', 'zip_code', 'make', 'model', 'objno', 'year', 'age', 'service_contract', 'ikz', 'kuerzel', 'address', 'note'),delimiter=';')
        for row in reader:
            if not line == 0:
                rd = dict(row)
                #myRules.append_rule(dict(row))
                try:
                    new = RuleWT()
                    new.lat = self.to_float(rd['lat'])
                    new.lng = self.to_float(rd['lng'])
                    new.radius = self.to_float(rd['radius'])
                    new.zip_code = self.check_empty_string(rd['zip_code'])
                    new.make = self.check_empty_string(rd['make'])
                    new.objno = self.check_empty_string(rd['objno'])
                    new.year = self.check_empty_string(rd['year'])
                    new.age = self.check_empty_string(rd['age'])
                    new.service_contract = self.check_empty_string(rd['service_contract'])
                    new.ikz = self.check_empty_string(rd['ikz'])
                    new.kuerzel = self.check_empty_string(rd['kuerzel'])
                    new.address = self.check_empty_string(rd['address'])
                    new.note = self.check_empty_string(rd['note'])
                    new.save()
                except Exception as e:
                    log.info("Rule Importer")
                    log.info(rd)
                    log.error(e)
            line += 1
        new.update_row_numbers()
        #myRules.save()

    def to_float(self, obj):
        try:
            return float(obj)
        except:
            return None

    def check_empty_string(self, obj):
        if obj == '':
            return None
        else:
            return str(obj)

class HealthCheck(View):
    template_name = "healthcheck.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                geocode_result = gmaps.geocode("")
            except googlemaps.exceptions.HTTPError as e:
                print(e)
            status_google = geocode_result[0]
            return render(request, self.template_name)
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
            user.delete()
            self.send_delete_mail(user)
            return Response(status=200)
        else:
            return Response(status=403)
    
    def activate(self, request, pk, *args, **kwargs):
        if request.user.has_perm('WZO_App.change_wzo_user'):
            user = WZO_User.objects.get(pk=pk)
            group = Group.objects.get(name='RIV-Manager')
            user.groups.add(group)
            user.save()
            self.send_activation_mail(user)
            return Response(status=202)
        else:
            return Response(status=403)
    
    def deactivate(self, request, pk, *args, **kwargs):
        if request.user.has_perm('WZO_App.change_wzo_user'):
            user = WZO_User.objects.get(pk=pk)
            group = Group.objects.get(name='RIV-Manager')
            user.groups.remove(group)
            user.save()
            self.send_deactivation_mail(user)
            return Response(status=202)
        else:
            return Response(status=403)

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

#DEPRECIATED!!!!!
class DEP_WTRules(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        with open(os.path.join(settings.MEDIA_ROOT, 'wt_rules', '20210418_182449' + '.json'), "r", encoding='utf-8') as f:
            self.jdata = json.load(f)
        params = request.GET
        if params:
            res = {
                'data': self.search(params)
            }
        else:
            res = {
                'data': self.jdata
            }
        return Response(res)
    
    def search(self, params):
        search = {}
        result = []
        for key in params:
            if key in ['make', 'workshop', 'address', 'note']:
                val = params.get(key, None)
                search[key] = val
        for i in self.jdata:
            if 'make' in search:
                m = self.check_make(i['rule']['make'],search['make'])
                if not m:
                    continue
            if 'workshop' in search:
                m = self.check_workshop(i['rule']['kuerzel'],search['workshop'])
                if not m:
                    continue
            if 'address' in search:
                m = self.check_address(i['rule']['address'],search['address'])
                if not m:
                    continue
            if 'note' in search:
                m = self.check_address(i['rule']['note'],search['note'])
                if not m:
                    continue
            result.append(i)
        return result
            

    def check_make(self, rule_make, param_make):
        if rule_make is None:
            return True
        elif param_make in rule_make:
            return True
        elif not param_make[0] == '%' and param_make[-1] == '%':
            return rule_make[0].startswith(param_make[:-1])
        elif param_make[0] == '%' and not param_make[-1] == '%':
            return rule_make[0].endswith(param_make[1:])
        else:
            return False

    def check_workshop(self, rule_ws, param_ws):
        if rule_ws is None:
            return True
        elif param_ws in rule_ws:
            return True
        else:
            return False
    
    def check_address(self, rule_address, param_address):
        if rule_address is None:
            return False
        elif param_address in rule_address:
            return True
        elif not param_address[0] == '%' and param_address[-1] == '%':
            return rule_address[0].startswith(param_address[:-1])
        elif param_address[0] == '%' and not param_address[-1] == '%':
            return rule_address[0].endswith(param_address[1:])
        else:
            return False

    def check_note(self, rule_note, param_note):
        if rule_note is None:
            return False
        elif param_note in rule_note:
            return True
        elif not param_note[0] == '%' and param_note[-1] == '%':
            return rule_note[0].startswith(param_note[:-1])
        elif param_note[0] == '%' and not param_note[-1] == '%':
            return rule_note[0].endswith(param_note[1:])
        else:
            return False
                
    



