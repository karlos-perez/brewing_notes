from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

# from nnmware.core.abstract import AbstractName
# from nnmware.core.models import NnmwareUser, LikeMixin


class BrewUser(AbstractUser):
# class BrewUser(NnmwareUser, LikeMixin):
    pass


# class BeerStyleCategory(AbstractName):
class BeerStyleCategory(models.Model):
    index = models.PositiveSmallIntegerField(verbose_name=_("Index"), blank=True, db_index=True)
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)

    slug_detail = 'style_category'

    class Meta:
        ordering = ['index', ]
        verbose_name = _('Beer Style Category')
        verbose_name_plural = _('Beer Style Categories')

    def __str__(self):
        return "%s" % self.name


class BeerStyle(models.Model):
# class BeerStyle(AbstractName):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')
    category = models.ForeignKey(BeerStyleCategory, verbose_name=_('Category'), null=True, blank=True, on_delete=models.PROTECT)
    index = models.CharField(verbose_name=_("Index"), max_length=255, blank=True, db_index=True, default='')
    aroma = models.TextField(verbose_name=_("Aroma"), blank=True, default='')
    appearance = models.TextField(verbose_name=_("Appearance"),  blank=True, default='')
    flavor = models.TextField(verbose_name=_("Flavor"),  blank=True, default='')
    mouthfeel = models.TextField(verbose_name=_("Mouthfeel"), blank=True, default='')
    comments = models.TextField(verbose_name=_("Comments"), blank=True, default='')
    history = models.TextField(verbose_name=_("History"), blank=True, default='')
    ingredients = models.TextField(verbose_name=_("Characteristic Ingredients"), blank=True, default='')
    comparison = models.TextField(verbose_name=_("Style Comparison"), blank=True, default='')
    OG_min = models.DecimalField(verbose_name=_("OG minimal"), max_digits=4, decimal_places=3)
    OG_max = models.DecimalField(verbose_name=_("OG maximal"), max_digits=4, decimal_places=3)
    FG_min = models.DecimalField(verbose_name=_("FG minimal"), max_digits=4, decimal_places=3)
    FG_max = models.DecimalField(verbose_name=_("FG maximal"), max_digits=4, decimal_places=3)
    ABV_min = models.DecimalField(verbose_name=_("ABV minimal"), max_digits=3, decimal_places=1)
    ABV_max = models.DecimalField(verbose_name=_("ABV maximal"), max_digits=3, decimal_places=1)
    IBUs_min = models.PositiveSmallIntegerField(verbose_name=_("IBUs minimal"),)
    IBUs_max = models.PositiveSmallIntegerField(verbose_name=_("IBUs maximal"),)
    SRM_min = models.PositiveSmallIntegerField(verbose_name=_("SRM minimal"),)
    SRM_max = models.PositiveSmallIntegerField(verbose_name=_("SRM maximal"),)

    class Meta:
        ordering = ['index', ]
        verbose_name = _('Beer Style')
        verbose_name_plural = _('Beer Styles')

    def __str__(self):
        return "%s" % self.name


class FermentablesCategory(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Fermentables Category')
        verbose_name_plural = _('Fermentables Categories')

    def __str__(self):
        return "%s" % self.name


class Country(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

    def __str__(self):
        return "%s" % self.name


class Company(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Company')
        verbose_name_plural = _('Company')

    def __str__(self):
        return "%s" % self.name


class Fermentables(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    category = models.ForeignKey(FermentablesCategory, verbose_name=_('Category'), null=True, blank=True,
                                 on_delete=models.PROTECT)
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')
    share = models.PositiveSmallIntegerField(verbose_name=_("Share up in percentage"),)
    color = models.PositiveSmallIntegerField(verbose_name=_("Color"), blank=False)
    extractivity = models.DecimalField(verbose_name=_("Extractivity"), max_digits=3, decimal_places=1, blank=False)
    protein = models.DecimalField(verbose_name=_("Protein"), max_digits=3, decimal_places=1, blank=False)
    country = models.ForeignKey(Country, verbose_name=_('Country'), null=True, blank=True, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, verbose_name=_('Company'), null=True, blank=True, on_delete=models.PROTECT)


    class Meta:
        ordering = ['category', 'name']
        verbose_name = _('Fermentable')
        verbose_name_plural = _('Fermentables')

    def __str__(self):
        return "%s" % self.name


class Steps(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Step')
        verbose_name_plural = _('Steps')

    def __str__(self):
        return "%s" % self.name



PELLETS = 0
LEAF_WHOLE = 1
LUPULIN_PELLET = 2

TYPE_HOPS = (
    (PELLETS, _('Pellet')),
    (LEAF_WHOLE, _('Leaf whole')),
    (LUPULIN_PELLET, _('Lupulin Pellet')),
)


class Hops(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    category = models.ForeignKey(FermentablesCategory, verbose_name=_('Category'), null=True, blank=True,
                                 on_delete=models.PROTECT)
    slug_name = models.SlugField(_("Slug_name"), max_length=255, blank=True)
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')
    type_hops = models.IntegerField(_("Type hops"), choices=TYPE_HOPS, default=PELLETS)
    alfa_acid = models.DecimalField(verbose_name=_("Protein"), max_digits=3, decimal_places=1, blank=False)
    country = models.ForeignKey(Country, verbose_name=_('Country'), null=True, blank=True, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, verbose_name=_('Company'), null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Hop')
        verbose_name_plural = _('Hops')

    def __str__(self):
        return "%s" % self.name
