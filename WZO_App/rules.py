import datetime
import logging
import json
import os
import decimal
from math import sqrt
from geopy import distance
from django.conf import settings
from .models import *
log = logging.getLogger(__name__)

class RuleBuilder():
    def __init__(self, kindof):
        self.check_kindof(kindof)
        self.rules = []
        self.filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.rows = 0

    def check_kindof(self, kindof):
        if kindof == "V":
            self.directory = "wt_rules"
        elif kindof == "U":
            self.directory = "acc_rules"
        else:
            raise BaseException("Not applicable")

    def append_rule(self, row):
        new = {
            "lat": self.to_float(row['lat']),
            "lng": self.to_float(row['lng']),
            "radius": self.to_float(row['radius']),
            "zip_code": self.to_arrayofstr(row['zip_code']),
            "make": self.to_arrayofstr(row['make']),
            "model": self.to_arrayofstr(row['model']),
            "objno": self.to_arrayofstr(row['objno']),
            "year": self.to_arrayofstr(row['year']),
            "age": self.to_arrayofstr(row['age']),
            "service_contract": self.to_boolean(row['service_contract']),
            "ikz": self.to_arrayofstr(row['ikz']),
            "kuerzel": self.to_arrayofstr(row['kuerzel']),
            "address": self.to_arrayofstr(row['address']),
            "note": self.to_arrayofstr(row['note'])
        }
        self.rows +=1 
        self.rules.append({"row": self.rows, "rule": new})

    def to_float(self, obj):
        try:
            return float(obj)
        except:
            return None

    def to_arrayofstr(self, obj):
        try:
            if obj == '':
                return None
            else:
                return obj.split(", ")
        except:
            return None

    def to_boolean(self,obj):
        try:
            if obj == "true" or obj == "True":
                return True
            elif obj == "false" or obj == "False":
                return False
        except:
            return None

    def print_rules(self):
        print(self.rules)

    def log_rules(self):
        log.info(self.rules)

    def save(self):
        with open(os.path.join(settings.MEDIA_ROOT, self.directory, self.filename + '.json'), "w", encoding='utf-8') as f:
            json.dump(self.rules,f)

class RuleEngine():
    def __init__(self,kindof,filename):
        self.kindof = kindof
        self.check_kindof(kindof)
        self.filename = filename
        self.open_rules()

    def check_kindof(self, kindof):
        if kindof == "V":
            self.directory = "wt_rules"
        elif kindof == "U":
            self.directory = "acc_rules"
        else:
            raise BaseException("Not applicable")
    
    def open_rules(self):
        with open(os.path.join(settings.MEDIA_ROOT, self.directory, self.filename + '.json'), "r", encoding='utf-8') as f:
            self.data = json.load(f)

    def run_rules(self):
        Allocation.objects.all().delete()
        vehicles = Vehicle.objects.all()
        for v in vehicles:
            log.debug('Vehicle IKZ: {}, Make: {}'.format(v.ikz, v.make))
            output = self.run_checks(v)
            if output is not None:
                log.debug('Output: {}'.format(output))
                w = Workshop.objects.get(kuerzel=output)
                new = Allocation.objects.create(a_type=self.kindof, v_id=v, w_id= w)
                new.save()

    def run_checks(self, veh):
        for row in self.data:
            in_circle = self.check_geo((row['rule']['lat'],row['rule']['lng']),row['rule']['radius'], (veh.eort.lat, veh.eort.lng))
            if not in_circle:
                continue
            in_plz = self.check_plz(row['rule']['zip_code'], veh.eort.zip_code)
            if not in_plz:
                continue
            in_make = self.check_make(row['rule']['make'], veh.make)
            if not in_make:
                continue
            in_model = self.check_model(row['rule']['model'], veh.model)
            if not in_model:
                continue
            in_objno = self.check_objno(row['rule']['objno'], veh.objno)
            if not in_objno:
                continue
            in_year = self.check_year(row['rule']['year'], veh.year)
            if not in_year:
                continue
            in_ikz = self.check_ikz(row['rule']['ikz'], veh.ikz)
            if not in_ikz:
                continue
            in_service_contract = self.check_service_contract(row['rule']['service_contract'], veh.service_contract)
            if not in_service_contract:
                continue
            in_age = self.check_age(row['rule']['age'], veh.age)
            if not in_age:
                continue
            if in_circle and in_plz and in_make and in_model and in_objno and in_year and in_ikz and in_service_contract and in_age:
                return row['rule']['kuerzel'][0]
        return None

    def check_geo(self, circle:tuple, radius:float, eort:tuple):
        if circle[0] is not None and circle[1] and radius is not None and eort[0] is not None and eort[1] is not None:
            dis = distance.distance(circle,eort).km
            log.info("Distance: {}km".format(dis))
            if dis <= radius:
                log.info('In Circle')
                return True
            else:
                log.info('Not in Circle')
                return False
        else:
            return True
    
    def check_plz(self, zip_code:list, eort_zip_code:str):
        log.info('Rule Zips: {}, Eort: {}'.format(zip_code,eort_zip_code))
        if not zip_code:
            return True
        else:
            for i in zip_code:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(eort_zip_code,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(eort_zip_code,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(eort_zip_code, i)
                else:
                    result = False
                if result:
                    break
            log.info('In PLZ {}'.format(result))
            return result

    def check_make(self, rule_make:list, veh_make:str):
        if not rule_make:
            return True
        else:
            for i in rule_make:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_make,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_make,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_make, i)
                else:
                    result = False
                if result:
                    break
            log.info('In Make {}'.format(result))
            return result

    def check_model(self, rule_model:list, veh_model:str):
        if not rule_model:
            return True
        else:
            for i in rule_model:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_model,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_model,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_model, i)
                else:
                    result = False
                if result:
                    break
            log.info('In Model {}'.format(result))
            return result

    def check_objno(self, rule_objno:list, veh_objno:str):
        if not rule_objno:
            return True
        else:
            for i in rule_objno:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_objno,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_objno,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_objno, i)
                else:
                    result = False
                if result:
                    break
            log.info('In ObjNo {}'.format(result))
            return result

    def check_year(self, rule_year:list, veh_year:str):
        if not rule_year:
            return True
        else:
            for i in rule_year:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_year,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_year,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_year, i)
                else:
                    result = False
                if result:
                    break
            log.info(result)
            return result

    def check_ikz(self, rule_ikz:list, veh_ikz:str):
        if not rule_ikz:
            return True
        else:
            for i in rule_ikz:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_ikz,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_ikz,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_ikz, i)
                else:
                    result = False
                if result:
                    break
            log.info(result)
            return result
    
    def check_service_contract(self, rule_sc, veh_sc):
        if not rule_sc:
            return True
        else:
            if rule_sc == veh_sc:
                return True
            else:
                return False

    def check_age(self, rule_age:list, veh_age:int):
        if not rule_age:
            return True
        else:
            i = rule_age[0]
            if i[0] == '<':
                result = self.lower(veh_age,i[1:])
            elif i[0] == '>':
                result =  self.greater(veh_age,i[1:])
            elif int(veh_age) == int(i):
                result = True
            else:
                result = False
            log.info('In Age {}'.format(result))
            return result

    def lower(self, x, y):
        x = int(x)
        y = int(y)
        if x < y:
            return True
        else:
            return False

    def greater(self, x, y):
        x = int(x)
        y = int(y)
        if x > y:
            return True
        else:
            return False

    def equal(self, x, y):
        if x == y:
            return True
        else:
            return False
    
    def starts_with(self, x, y):
        return x.startswith(y)

    def ends_with(self, x, y):
        return x.endswith(y)

class RuleEngineWT(): 
    def __init__(self):
        self.rulesQS = RuleWT.objects.all().order_by('row')

    def run_rules(self):
        Allocation.objects.all().delete()
        vehicles = Vehicle.objects.all()
        for v in vehicles:
            log.debug('Vehicle IKZ: {}, Make: {}'.format(v.ikz, v.make))
            output = self.run_checks(v)
            if output is not None:
                log.debug('Output: {}'.format(output))
                w = Workshop.objects.get(kuerzel=output)
                new = Allocation.objects.create(a_type='V', v_id=v, w_id= w)
                new.save()

    def to_arrayofstr(self, obj):
        try:
            if obj:
                return obj.split(", ")
        except:
            return obj

    def run_checks(self, veh):
        for row in self.rulesQS:
            in_circle = self.check_geo((row.lat,row.lng),row.radius, (veh.eort.lat, veh.eort.lng))
            if not in_circle:
                continue
            in_plz = self.check_plz(self.to_arrayofstr(row.zip_code), veh.eort.zip_code)
            if not in_plz:
                continue
            in_make = self.check_make(self.to_arrayofstr(row.make), veh.make)
            if not in_make:
                continue
            in_model = self.check_model(self.to_arrayofstr(row.model), veh.model)
            if not in_model:
                continue
            in_objno = self.check_objno(self.to_arrayofstr(row.objno), veh.objno)
            if not in_objno:
                continue
            in_year = self.check_year(self.to_arrayofstr(row.year), veh.year)
            if not in_year:
                continue
            in_ikz = self.check_ikz(self.to_arrayofstr(row.ikz), veh.ikz)
            if not in_ikz:
                continue
            in_service_contract = self.check_service_contract(row.service_contract, veh.service_contract)
            if not in_service_contract:
                continue
            in_age = self.check_age(row.age, veh.age)
            if not in_age:
                continue
            if in_circle and in_plz and in_make and in_model and in_objno and in_year and in_ikz and in_service_contract and in_age:
                return row.kuerzel
        return None

    def check_geo(self, circle:tuple, radius:float, eort:tuple):
        if circle[0] is not None and circle[1] and radius is not None and eort[0] is not None and eort[1] is not None:
            dis = distance.distance(circle,eort).m
            log.info("Distance: {}m, Radius {}m".format(dis,radius))
            if dis <= radius:
                log.info('In Circle')
                return True
            else:
                log.info('Not in Circle')
                return False
        else:
            return True
    
    def check_plz(self, zip_code:list, eort_zip_code:str):
        log.info('Rule Zips: {}, Eort: {}'.format(zip_code,eort_zip_code))
        if not zip_code:
            return True
        else:
            for i in zip_code:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(eort_zip_code,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(eort_zip_code,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(eort_zip_code, i)
                else:
                    result = False
                if result:
                    break
            log.info('In PLZ {}'.format(result))
            return result

    def check_make(self, rule_make:list, veh_make:str):
        if not rule_make:
            return True
        else:
            for i in rule_make:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_make,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_make,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_make, i)
                else:
                    result = False
                if result:
                    break
            log.info('In Make {}'.format(result))
            return result

    def check_model(self, rule_model:list, veh_model:str):
        if not rule_model:
            return True
        else:
            for i in rule_model:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_model,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_model,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_model, i)
                else:
                    result = False
                if result:
                    break
            log.info('In Model {}'.format(result))
            return result

    def check_objno(self, rule_objno:list, veh_objno:str):
        if not rule_objno:
            return True
        else:
            for i in rule_objno:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_objno,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_objno,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_objno, i)
                else:
                    result = False
                if result:
                    break
            log.info('In ObjNo {}'.format(result))
            return result

    def check_year(self, rule_year:list, veh_year:str):
        if not rule_year:
            return True
        else:
            for i in rule_year:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_year,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_year,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_year, i)
                else:
                    result = False
                if result:
                    break
            log.info(result)
            return result

    def check_ikz(self, rule_ikz:list, veh_ikz:str):
        if not rule_ikz:
            return True
        else:
            for i in rule_ikz:
                if i[0] == '%' and not i[-1] == '%':
                    result = self.ends_with(veh_ikz,i[1:])
                elif not i[0] == '%' and i[-1] == '%':
                    result =  self.starts_with(veh_ikz,i[:-1])
                elif not i[0] == '%' and not i[-1] == '%':
                    result =  self.equal(veh_ikz, i)
                else:
                    result = False
                if result:
                    break
            log.info(result)
            return result

    def translate_boolean(self, boolean_text):
        if boolean_text == 'true' or boolean_text == 'True' or boolean_text == 'TRUE':
            return True
        elif boolean_text == 'false' or boolean_text == 'False' or boolean_text == 'FALSE':
            return False
        else:
            None
    
    def check_service_contract(self, rule_sc_text, veh_sc):
        rule_sc = self.translate_boolean(rule_sc_text)
        if not rule_sc:
            return True
        else:
            if rule_sc == veh_sc:
                return True
            else:
                return False

    def check_age(self, rule_age:list, veh_age:int):
        if not rule_age:
            return True
        else:
            i = rule_age[0]
            if i[0] == '<':
                result = self.lower(veh_age,i[1:])
            elif i[0] == '>':
                result =  self.greater(veh_age,i[1:])
            elif int(veh_age) == int(i):
                result = True
            else:
                result = False
            log.info('In Age {}'.format(result))
            return result

    def lower(self, x, y):
        x = int(x)
        y = int(y)
        if x < y:
            return True
        else:
            return False

    def greater(self, x, y):
        x = int(x)
        y = int(y)
        if x > y:
            return True
        else:
            return False

    def equal(self, x, y):
        if x == y:
            return True
        else:
            return False
    
    def starts_with(self, x, y):
        return x.startswith(y)

    def ends_with(self, x, y):
        return x.endswith(y)

