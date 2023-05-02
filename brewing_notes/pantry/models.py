from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from catalog.models import Malt, Fermentable, Hops, Misc, Yeasts

from brew.constants import MEASURE, GRAM
from brew.models import Recipe


class Pantry(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.CASCADE)
    enabled = models.BooleanField(verbose_name=_("Enabled in system"), default=False, db_index=True)
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')

    class Meta:
        ordering = ['user']
        verbose_name = _('Pantry user')
        verbose_name_plural = _('Pantry users')


class AbstractReserve(models.Model):
    pantry = models.ForeignKey(Pantry, verbose_name=_('Pantry'), on_delete=models.CASCADE)
    created_date = models.DateField(_("Created date"), auto_now=False, auto_now_add=False, null=True, blank=True)
    expiration_date = models.DateField(_("Experation date"), auto_now=False, auto_now_add=False, null=True, blank=True)
    spent = models.BooleanField(verbose_name=_("Spent"), default=False, db_index=True)
    supplier = models.CharField(verbose_name=_("The supplier"), max_length=255, blank=True, default='')
    note = models.TextField(verbose_name=_("Note"), blank=True, default='')
    cost_per_unit = models.DecimalField(verbose_name=_('Cost per unit'), max_digits=8, decimal_places=2, default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.balance == 0:
            self.spent = True
        super().save(*args, **kwargs)


class MaltsReserve(AbstractReserve):
    malt = models.ForeignKey(Malt, verbose_name=_('Malt'), on_delete=models.CASCADE)
    extractivity = models.DecimalField(verbose_name=_("Extractivity"), max_digits=3, decimal_places=1, default=0)
    parish = models.DecimalField(verbose_name=_('Parish amount in kg'), max_digits=5, decimal_places=2, default=0)
    balance = models.DecimalField(verbose_name=_('Balance amount in kg'), max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']
        verbose_name = _('Malt reserve')
        verbose_name_plural = _('Malts reserve')


class FermentableReserve(AbstractReserve):
    fermentable = models.ForeignKey(Fermentable, verbose_name=_('Fermentable'), on_delete=models.CASCADE)
    parish = models.DecimalField(verbose_name=_('Parish amount'), max_digits=5, decimal_places=2, default=0)
    balance = models.DecimalField(verbose_name=_('Balance amount'), max_digits=5, decimal_places=2, default=0)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)

    class Meta:
        ordering = ['fermentable']
        verbose_name = _('Fermentable reserve')
        verbose_name_plural = _('Fermentables reserve')


class HopsReserve(AbstractReserve):
    hop = models.ForeignKey(Hops, verbose_name=_('Hop'), on_delete=models.CASCADE)
    alfa = models.DecimalField(verbose_name=_('Alfa acid'), max_digits=3, decimal_places=1, default=0)
    parish = models.PositiveIntegerField(verbose_name=_('Parish amount in g'), default=0)
    balance = models.PositiveIntegerField(verbose_name=_('Balance amount in g'), default=0)

    class Meta:
        ordering = ['hop']
        verbose_name = _('Hop reserve')
        verbose_name_plural = _('Hops reserve')


class YeastsReserve(AbstractReserve):
    yeast = models.ForeignKey(Yeasts, verbose_name=_('Yeast'), on_delete=models.CASCADE)
    parish = models.DecimalField(verbose_name=_('Parish amount'), max_digits=5, decimal_places=2, default=0)
    balance = models.DecimalField(verbose_name=_('Balance amount'), max_digits=5, decimal_places=2, default=0)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)

    class Meta:
        ordering = ['yeast']
        verbose_name = _('Yeast reserve')
        verbose_name_plural = _('Yeasts reserve')


class MiscReserve(AbstractReserve):
    misc = models.ForeignKey(Misc, verbose_name=_('Misc'), on_delete=models.CASCADE)
    parish = models.DecimalField(verbose_name=_('Parish amount'), max_digits=5, decimal_places=2, default=0)
    balance = models.DecimalField(verbose_name=_('Balance amount'), max_digits=5, decimal_places=2, default=0)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)

    class Meta:
        ordering = ['misc']
        verbose_name = _('Misc reserve')
        verbose_name_plural = _('Misc reserve')


class AbstractWriteOff(models.Model):
    pantry = models.ForeignKey(Pantry, verbose_name=_('Pantry'), on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, verbose_name=_('Recipe'), null=True, blank=False, on_delete=models.PROTECT)
    cost = models.DecimalField(verbose_name=_('Cost'), max_digits=9, decimal_places=2, default=0)
    note = models.TextField(verbose_name=_('Note'), blank=True, default='')
    date = models.DateField(_("Date"), auto_now=False, auto_now_add=False, null=True, blank=True)

    class Meta:
        abstract = True


class MaltsWriteOff(AbstractWriteOff):
    malt_reserve = models.ForeignKey(MaltsReserve, verbose_name=_('Malt'), on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name=_('Amount in kg'), max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']
        verbose_name = _('Malt write-off')
        verbose_name_plural = _('Malts write-off')


class FermentableWriteOff(AbstractWriteOff):
    fermentable_reserve = models.ForeignKey(FermentableReserve, verbose_name=_('Fermentable'), on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name=_('Amount'), default=0)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)

    class Meta:
        ordering = ['id']
        verbose_name = _('Fermentable write-off')
        verbose_name_plural = _('Fermentables write-off')


class HopsWriteOff(AbstractWriteOff):
    hop_reserve = models.ForeignKey(HopsReserve, verbose_name=_('Hops'), on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name=_('Amount in g'), default=0)

    class Meta:
        ordering = ['id']
        verbose_name = _('Hop write-off')
        verbose_name_plural = _('Hops write-off')


class YeastsWriteOff(AbstractWriteOff):
    yeast_reserve = models.ForeignKey(YeastsReserve, verbose_name=_('Yeast'), on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name=_('Amount'), default=0)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)

    class Meta:
        ordering = ['id']
        verbose_name = _('Yeast write-off')
        verbose_name_plural = _('Yeasts write-off')


class MiscWriteOff(AbstractWriteOff):
    misc_reserve = models.ForeignKey(MiscReserve, verbose_name=_('Misc'), on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name=_('Amount'), default=0)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)

    class Meta:
        ordering = ['id']
        verbose_name = _('Misc write-off')
        verbose_name_plural = _('Misc write-off')

