from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from nnmware.core.models import AbstractIP

from brew.models import ConnectedDevice, Modules


class DeviceDataLog(models.Model):
    device = models.ForeignKey(ConnectedDevice, verbose_name=_('Device'), on_delete=models.PROTECT)
    ip = models.GenericIPAddressField(verbose_name=_('IP'), null=True, blank=True)
    created_date = models.DateTimeField(verbose_name=_("Created date"), default=now)
    beer_temp = models.DecimalField(verbose_name=_('Beer temperature'), max_digits=4, decimal_places=2, default=0)
    fridge_temp = models.DecimalField(verbose_name=_('Fridge temperature'), max_digits=4, decimal_places=2, default=0)
    room_temp = models.DecimalField(verbose_name=_('Room temperature'), max_digits=4, decimal_places=2, default=0)
    aux_temp = models.DecimalField(verbose_name=_('Auxiliary temperature'), max_digits=4, decimal_places=2, default=0)
    gravity = models.DecimalField(verbose_name=_('Gravity'), max_digits=4, decimal_places=3, default=1.000)
    tilt = models.DecimalField(verbose_name=_('Tilt angle'), max_digits=4, decimal_places=2, default=0)
    voltage = models.DecimalField(verbose_name=_('Voltage'), max_digits=4, decimal_places=2, default=0)
    pressure = models.DecimalField(verbose_name=_('Pressure'), max_digits=4, decimal_places=2, default=0)
    rssi = models.SmallIntegerField(_('RSSI in dBm'), default=-100)

    class Meta:
        ordering = ['-created_date']
        verbose_name = _('Device data log')
        verbose_name_plural = _('Device data logs')

    def __str__(self):
        if self.device:
            return f'{self.device.token}'
        else:
            return f'{self.pk}'


class DeviceRawData(AbstractIP):
    token = models.CharField(_('Token'), max_length=20, default='')
    date = models.DateTimeField(verbose_name=_("Date"), default=now)
    hostname = models.CharField(verbose_name=_('Hostname'), max_length=100, db_index=True)
    referer = models.TextField(verbose_name=_('Referer'))
    url = models.CharField(verbose_name=_('URL'), max_length=255, db_index=True)
    body = models.TextField(verbose_name=_('POST data'))

    class Meta:
        ordering = ['-date']
        verbose_name = _("Device raw data")
        verbose_name_plural = _("Device raw data")


class ModuleDataLog(models.Model):
    module = models.ForeignKey(Modules, verbose_name=_('Module'), on_delete=models.PROTECT)
    date = models.DateTimeField(verbose_name=_("Date"), default=now)
    timestamp = models.IntegerField(verbose_name=_("Timestamp"), default=0)
    temperature = models.DecimalField(verbose_name=_('Temperature'), max_digits=5, decimal_places=2, default=0)
    relay_state = models.BooleanField(verbose_name=_("Relay state"), default=False)
    sensor_id = models.CharField(_('Sensor ID'), max_length=20, default='')
    chip_id = models.CharField(_('Token'), max_length=30, default='')
    version = models.CharField(_('Version'), max_length=30, default='')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Module data log')
        verbose_name_plural = _('Module data logs')

    def __str__(self):
        if self.module:
            return f'{self.module.token}'
        else:
            return f'{self.pk}'