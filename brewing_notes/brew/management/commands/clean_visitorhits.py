from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from nnmware.core.models import VisitorHit

from logdata.models import DeviceRawData, ModuleDataLog, DeviceDataLog


class Command(BaseCommand):
    def handle(self, *args, **options):
        time_threshold = timezone.now() - timedelta(days=7)
        VisitorHit.objects.filter(date__lt=time_threshold).delete()
        DeviceRawData.objects.filter(date__lt=time_threshold).delete()
        time_threshold_module = timezone.now() - timedelta(days=2)
        ModuleDataLog.objects.filter(date__lt=time_threshold_module).delete()
        time_threshold_device = timezone.now() - timedelta(days=45)
        DeviceDataLog.objects.filter(date__lt=time_threshold_device).delete()
