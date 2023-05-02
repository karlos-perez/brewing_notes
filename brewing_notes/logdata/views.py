import json
import logging
from datetime import timedelta, datetime

from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.generic import View

from brew.models import ConnectedDevice, Modules
from brew.utils import plato_gravity

from brewing_notes.celery import app

from .models import DeviceDataLog, ModuleDataLog


logger = logging.getLogger(__name__)


def is_none(a):
    if a is None:
        return 0
    else:
        return a

def clean_temp(t):
    temp = is_none(t)
    if abs(temp) > 50:
        temp = 0
    return temp


class BrewPiLessLogsRecordView(View):
    """
    Add log record BrewPiLess
    json: {"tempUnit":"C","beerTemp":%b,"fridgeTemp":%f,"roomTemp":%r,"gravity":%g,"tiltVal":%t,"auxTemp":%a,"extDVolt":%v,"pressure":%P,}
    """
    def post(self, request):
        try:
            token = request.GET.get('token', None)
            if token is None:
                raise ValueError
            trott = cache.get(f'TROTTLING_{token}')
            if trott is None:
                cache.add(f'TROTTLING_{token}',
                          timezone.now().strftime("%Y%m%d %H:%M:%S"),
                          settings.TROTTLING_LOG - settings.TROTTLING_OFFSET)
            else:
                # logger.error(f'Too frequent requests ({token}). Set Log time period {settings.TROTTLING_LOG} seconds:'
                #              f' {trott} | {timezone.now().strftime("%Y%m%d %H:%M:%S")}')
                return JsonResponse({'status': 'error',
                                     'error': f'Too frequent requests. Set Log time period {settings.TROTTLING_LOG} seconds'})
            req = json.loads(request.body.decode('UTF-8'))
            if req['tempUnit'] == 'C':
                try:
                    device = ConnectedDevice.objects.get(token=token)
                    if device.active and device.enabled:
                        time_threshold = timezone.now() - timedelta(days=device.user.records_limit)
                        results = device.devicedatalog_set.filter(created_date__lt=time_threshold)
                        results.delete()
                        log = DeviceDataLog()
                        log.device = device
                        beer_temp = clean_temp(req.get('beerTemp', None))
                        log.beer_temp = beer_temp
                        fridge_temp = clean_temp(req.get('fridgeTemp', None))
                        log.fridge_temp = fridge_temp
                        room_temp = clean_temp(req.get('roomTemp', None))
                        log.room_temp = room_temp
                        aux_temp = clean_temp(req.get('auxTemp', None))
                        log.aux_temp = aux_temp
                        gravity = is_none(req.get('gravity', None))
                        if gravity == 0 or gravity > 1.3:
                            gravity = 1.000
                        log.gravity = gravity
                        pressure = is_none(req.get('pressure', None))
                        if abs(pressure) > 60:
                            pressure = 0
                        log.pressure = pressure
                        tilt = is_none(req.get('tiltVal', None))
                        if abs(tilt) > 360:
                            tilt = 0
                        log.tilt = tilt
                        voltage = is_none(req.get('extDVolt', None))
                        if voltage < 0 or voltage > 12:
                            voltage = 0
                        log.voltage = voltage
                        log.ip = request.META['REMOTE_ADDR']
                        log.save()
                        last_data = {'time': log.created_date,
                                     'beer_temp': beer_temp,
                                     'fridge_temp': is_none(req['fridgeTemp']),
                                     'aux_temp': is_none(req['auxTemp']),
                                     'tilt': is_none(req['tiltVal']),
                                     'volt': is_none(req['extDVolt']),
                                     'pressure': is_none(req['pressure']),
                                     'root_temp': is_none(req['roomTemp']),
                                     'gravity': is_none(req['gravity'])}
                        cache.set(token, last_data, None)
                        return JsonResponse({'status': 'ok'})
                    else:
                        return JsonResponse({'status': 'error', 'error': 'Device not active|enabled'})
                except ConnectedDevice.DoesNotExist:
                    return JsonResponse({'status': 'error', 'error': 'Device not found'})
            else:
                logger.error(f'Temp Unit is not Celcius: {token} - {req} - {request.body.decode("UTF-8")}')
                return JsonResponse({'status': 'error', 'error': 'temp Unit is not Celcius'})
        except Exception as err:
            logger.error(f'Error save BPL log: {err} - {token} - {req} - {request.body.decode("UTF-8")}')
            return JsonResponse({'error': request.body.decode('UTF-8')})


class iSpindelLogsRecordView(View):
    """
    Add log record iSpindel
    """
    def post(self, request, *args, **kwargs):
        try:
            token = request.GET.get('token', None)
            if token is None:
                raise ValueError
            trott = cache.get(f'TROTTLING_{token}')
            if trott is None:
                cache.add(f'TROTTLING_{token}',
                          timezone.now().strftime("%Y%m%d %H:%M:%S"),
                          settings.TROTTLING_LOG - settings.TROTTLING_OFFSET)
            else:
                # logger.error(f'Too frequent requests . Set Log time period {settings.TROTTLING_LOG} seconds:'
                #              f' {trott} | {timezone.now().strftime("%Y%m%d %H:%M:%S")}')
                return JsonResponse({'status': 'error',
                                     'error': f'Too frequent requests.'
                                              f' Set Log time period {settings.TROTTLING_LOG} seconds'})
            req = json.loads(request.body.decode('UTF-8'))
            if req['temp_units'] == 'C':
                # device = get_object_or_404(ConnectedDevice, token=token, enabled=True, active=True)
                try:
                    device = ConnectedDevice.objects.get(token=token)
                    if device.active and device.enabled:
                        time_threshold = timezone.now() - timedelta(days=device.user.records_limit)
                        results = device.devicedatalog_set.filter(created_date__lt=time_threshold)
                        results.delete()
                        log = DeviceDataLog()
                        log.device = device
                        aux_temp = clean_temp(req.get('temperature', None))
                        log.aux_temp = aux_temp
                        gravity = is_none(req.get('gravity', None))
                        if gravity == 0 or gravity > 1.3:
                            gravity = 1.000
                        log.gravity = gravity
                        tilt = is_none(req.get('angle', None))
                        if abs(tilt) > 360:
                            tilt = 0
                        log.tilt = tilt
                        voltage = is_none(req.get('battery', None))
                        if voltage < 0 or voltage > 12:
                            voltage = 0
                        log.voltage = voltage
                        rssi = is_none(req.get('RSSI', None))
                        if abs(rssi) > 120:
                            rssi = 0
                        log.rssi = rssi
                        log.ip = request.META['REMOTE_ADDR']
                        log.save()
                        last_data = {'time': log.created_date,
                                     'aux_temp': is_none(req['temperature']),
                                     'tilt': is_none(req['angle']),
                                     'volt': is_none(req['battery']),
                                     'rssi': is_none(req['RSSI']),
                                     'gravity': round(is_none(req['gravity']), 3)}
                        cache.set(token, last_data, None)
                        return JsonResponse({'status': 'ok'})
                    else:
                        return JsonResponse({'status': 'error', 'error': 'Device not active|enabled'})
                except ConnectedDevice.DoesNotExist:
                    return JsonResponse({'status': 'error', 'error': 'Device not found'})
            else:
                logger.error(f'Temp Unit is not Celcius: {token} - {req} - {request.body.decode("UTF-8")}')
                return JsonResponse({'status': 'error', 'error': 'temp Unit is not Celcius'})
        except Exception as err:
            logger.error(f'Error save iSpindel log: {err} - {token} - {req} - {request.body.decode("UTF-8")}')
            return JsonResponse({'error': request.body.decode('UTF-8')})

# FLOATY
### ERROR  Error save iSpindel log: 'temp_units' - DGM5cPkKu6pX0g - {'floaty': {'name': 'Floaty-BrewsCrew', 'unit_temp': 'celsius', 'unit_grav': 'SG', 'datas': [{'time_second': 1636358824, 'temp': 29.2, 'grav': 1032}]}} - {"floaty":{"name":"Floaty-BrewsCrew","unit_temp":"celsius","unit_grav":"SG","datas":[{"time_second":1636358824,"temp":29.2,"grav":1032}]}}
# {"floaty":{"name":"Floaty-BrewsCrew",
#            "unit_temp":"celsius",
#            "unit_grav":"SG",
#            "datas":[{"time_second":1636358824,"temp":29.2,"grav":1032}]}


# Logging mode Module:
# 0 - None
# 11 - Fermenter Cooler
# 12 - Fermenter Heater
MODE_LOGGING = [11, 12]


def module_record(data):
    payload = json.loads(data.decode('UTF-8'))
    token = payload.get('token', None)
    active = payload.get('active', False)
    mode = payload.get('mode', 0)
    if token is not None and cache.get(token) is None:
        if active and mode in MODE_LOGGING:
            try:
                module = Modules.objects.get(token=token)
                if module.active and module.enabled:
                    log, created = ModuleDataLog.objects.get_or_create(module=module, timestamp=payload['ts'])
                    if created:
                        # log.module = module
                        log.temperature = payload['current_temp']
                        if payload['relay'] == 1:
                            log.relay_state = True
                        else:
                            log.relay_state = False
                        log.sensor_id = payload['info']['sensor_id']
                        log.chip_id = payload['info']['chip_id']
                        log.version = payload['info']['version']
                        log.save()
                        last_data = {'time': log.timestamp,
                                     'temp': log.temperature,
                                     'relay': log.relay_state}
                        cache.set(token, last_data, settings.TROTTLING_LOG_MODULE)
            except ObjectDoesNotExist:
                pass


from .mqtt import mqtt_run

mqtt_run()
