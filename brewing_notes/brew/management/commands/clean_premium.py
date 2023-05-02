from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from brew.constants import MODERATOR, PREMIUM, USER
from brew.models import BrewUser, ConnectedDevice, Modules, EquipmentModules, UserTelegramProfile
from logdata.models import DeviceRawData, ModuleDataLog, DeviceDataLog
from pantry.models import MaltsReserve, FermentableReserve, HopsReserve, YeastsReserve, MiscReserve, MaltsWriteOff, \
                          FermentableWriteOff, HopsWriteOff, YeastsWriteOff, MiscWriteOff


class Command(BaseCommand):
    """
    Clearing user data after the end of 30 days of premium access
    """
    def handle(self, *args, **options):
        time_threshold = timezone.now() - timedelta(days=31)
        users = BrewUser.objects.filter(premium_end__lt=time_threshold)
        for u in users:
            if u.status >= MODERATOR:
                u.premium_end = None
                u.save()
                continue
            elif u.status == PREMIUM:
                u.status = USER
                u.limit_draft = 5
                u.editor = False
                u.tester = False
            u.device_on_dashboard = None
            u.premium_end = None
            u.save()
            UserTelegramProfile.objects.filter(user=u).delete()
            devices = ConnectedDevice.objects.filter(user=u)
            for d in devices:
                DeviceDataLog.objects.filter(device=d).delete()
                d.delete()
            equipments = EquipmentModules.objects.filter(user=u)
            for e in equipments:
                e.delete()
            modules = Modules.objects.filter(user=u)
            for m in modules:
                ModuleDataLog.objects.filter(module=m).delete()
                m.delete()
            if hasattr(u, 'pantry'):
                up = u.pantry
                MaltsReserve.objects.filter(pantry=up).delete()
                FermentableReserve.objects.filter(pantry=up).delete()
                HopsReserve.objects.filter(pantry=up).delete()
                YeastsReserve.objects.filter(pantry=up).delete()
                MiscReserve.objects.filter(pantry=up).delete()
                MaltsWriteOff.objects.filter(pantry=up).delete()
                FermentableWriteOff.objects.filter(pantry=up).delete()
                HopsWriteOff.objects.filter(pantry=up).delete()
                YeastsWriteOff.objects.filter(pantry=up).delete()
                MiscWriteOff.objects.filter(pantry=up).delete()


