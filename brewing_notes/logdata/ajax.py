import json
import logging
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse

from nnmware.core.ajax import ajax_answer_lazy
from nnmware.core.exceptions import AccessError

from brew.models import ConnectedDevice, EquipmentModules

from .models import DeviceDataLog, ModuleDataLog

logger = logging.getLogger(__name__)


def device_chart(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        device = get_object_or_404(ConnectedDevice, pk=object_id, enabled=True, active=True)
        if device.user == request.user or request.user.is_superuser:
            logs = DeviceDataLog.objects.filter(device=device).order_by('-created_date')
            time_ = list()
            beer = list()
            fridge = list()
            room = list()
            aux = list()
            gravity = list()
            press = list()
            tilt = list()
            volt = list()
            rssi = list()
            for i in logs:
                time_.append(timezone.localtime(i.created_date))
                beer.append(float(i.beer_temp))
                fridge.append(float(i.fridge_temp))
                room.append(float(i.room_temp))
                aux.append(float(i.aux_temp))
                gravity.append(float(i.gravity))
                press.append(float(i.pressure))
                tilt.append(float(i.tilt))
                volt.append(float(i.voltage))
                rssi.append(float(i.rssi))
            payload = {'success': True,
                       'date': time_,
                       'beer': beer,
                       'fridge': fridge,
                       'room': room,
                       'aux': aux,
                       'grav': gravity,
                       'press': press,
                       'tilt': tilt,
                       'volt': volt,
                       'rssi': rssi,
                       }
        else:
            raise AccessError
    except Exception as err:
        logger.error(f'Ajax get log device: {err}, user: {request.user.username}, device: {object_id}')
        payload = {'success': False, 'error': 'Error get log device', 'err': {err}}
    return HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder), content_type="application/json")


def equipment_chart(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        equipment = get_object_or_404(EquipmentModules, pk=object_id, enabled=True)
        if equipment.user == request.user or request.user.is_superuser:
            time_threshold = timezone.now() - timedelta(days=1)
            logs_main = equipment.main.moduledatalog_set.filter(date__gt=time_threshold).order_by('timestamp')
            time_main = list()
            temp_main = list()
            relay_main = list()
            for i in logs_main:
                time_main.append(i.timestamp)
                temp_main.append(float(i.temperature))
                if i.relay_state:
                    relay_main.append(1)
                else:
                    relay_main.append(0)
            payload = {'success': True,
                       'date_main': time_main,
                       'temp_main': temp_main,
                       'relay_main': relay_main}
            if equipment.second:
                logs_second = equipment.second.moduledatalog_set.filter(date__gt=time_threshold).order_by('timestamp')
                time_second = list()
                relay_second = list()
                for i in logs_second:
                    time_second.append(i.timestamp)
                    temp_main.append(float(i.temperature))
                    if i.relay_state:
                        relay_second.append(1)
                    else:
                        relay_second.append(0)
                second = {'date_second': time_second,
                          'relay_second': relay_second}
                payload.update(second)
        else:
            raise AccessError
    except Exception as err:
        logger.error(f'Ajax get log equipment: {err}, user: {request.user.username}, device: {object_id}')
        payload = {'success': False, 'error': 'Error get log equipment', 'err': {err}}
    return HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder), content_type="application/json")
