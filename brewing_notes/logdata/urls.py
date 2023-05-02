from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .ajax import *
from .views import *


urlpatterns = [
    path('brewpiless', csrf_exempt(BrewPiLessLogsRecordView.as_view()), name='bpl_log_record'),
    path('ispindel', csrf_exempt(iSpindelLogsRecordView.as_view()), name='iSp_log_record'),

    path('api/v1/device/<int:object_id>/chart/', device_chart, name='device_chart'),
    path('api/v1/equipment/<int:object_id>/chart/', equipment_chart, name='equipment_chart'),
]