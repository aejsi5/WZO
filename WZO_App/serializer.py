from rest_framework import serializers
from .models import *
from datetime import datetime
from django.db.models import Count
import json


class City_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Zip_Code
        fields = ['zip_code', 'city', 'state']

class Veh_Serializer(serializers.ModelSerializer):
    wt_workshop = serializers.SerializerMethodField()
    acc_workshop = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_wt_workshop(self, obj):
        allo = Allocation.objects.filter(v_id=obj, a_type='V')
        if allo:
            wid = allo.values('w_id')[0]['w_id']
            w = Workshop.objects.filter(pk=wid)
            return w.values()[0]
        else:
            return None

    def get_acc_workshop(self, obj):
        allo = Allocation.objects.filter(v_id=obj, a_type='U')
        if allo:
            wid = allo.values('w_id')[0]['w_id']
            w = Workshop.objects.filter(pk=wid)
            return w.values()[0]
        else:
            return None

class Workshop_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Workshop
        fields = '__all__'

class Allocation_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = '__all__'

class VehAllo_Serializer(serializers.ModelSerializer):
    workshops = serializers.SerializerMethodField()
    class Meta:
        model = Vehicle
        fields = ['workshops']
    
    def get_workshops(self, obj):
        result = []
        allo = Allocation.objects.filter(v_id=obj.veh_id).values('w_id', 'a_type')
        for w in allo:
            workshop = Workshop.objects.filter(w_id=w['w_id']).values()
            city = Zip_Code.objects.get(pk=workshop[0]['city_id'])
            d = workshop[0].copy()
            d['city'] = city.city
            d['type'] = w['a_type']
            d.pop('city_id', None)
            result.append(d)
        return result
    
class Eort_Serializer(serializers.ModelSerializer):
    #vehicles = serializers.SerializerMethodField()
    make_list = serializers.SerializerMethodField()
    has_vehicle = serializers.SerializerMethodField()
    context = serializers.SerializerMethodField()
    city = City_Serializer()

    class Meta:
        model = Eort
        fields = ['eort_id', 'fm_eort_id', 'lat', 'lng', 'name', 'street', 'zip_code', 'city', 'region', 'context', 'has_vehicle', 'make_list']

    def get_vehicles(self, obj):
        return Vehicle.objects.filter(eort=obj.eort_id).values()

    def get_make_list(self, obj):
        return Vehicle.objects.filter(eort=obj).values('make').annotate(total=Count('make')).order_by('total')

    def get_has_vehicle(self, obj):
        vlist = Vehicle.objects.filter(eort=obj)
        if vlist:
            return True
        else:
            return False

    def get_context(self, obj):
        return {
            'titel': obj.name,
            'adress': '<p>' + self.check_None(obj.street) + '<br>' + self.check_None(obj.zip_code) + ' ' + self.check_None(obj.city.city) + '</p>'
        }
    
    def check_None(self, to_check):
        if to_check is not None:
            return to_check
        else:
            return ''

class RuleWT_Serializer(serializers.ModelSerializer):
    class Meta:
        model = RuleWT
        fields= '__all__'