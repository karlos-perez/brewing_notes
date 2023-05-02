from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from .constants import TYPE_HOPS, PELLETS, TYPE_ADDITIVE, SPICE, TYPE_YEASTS, ALE, FLOCCULATION, UNKNOWN, \
    TYPE_GRAIN, TYPE_FERMENTABLE, BASE_MALT, SUGAR, TYPE_BEER, SPECIAL_BEER, MALT_CATEGORY, \
    CATEGORY_BASE_MALT, BEER_STYLE_GUIDELINES, BJCP_2015


DEFAULT_GUIDES = BJCP_2015


class AbstractName(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')
    slug = models.CharField(verbose_name=_('URL-identifier'), max_length=100, blank=True, db_index=True, default='')

    class Meta:
        ordering = ['name']
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            if not self.id:
                super().save(*args, **kwargs)
            self.slug = self.id
        else:
            self.slug = str(self.slug).strip().replace(' ', '-')
        super().save(*args, **kwargs)


class AbstractWater(models.Model):
    calcum = models.PositiveSmallIntegerField(verbose_name=_('Calcum'), default=0, blank=False)
    bicarbonate = models.PositiveSmallIntegerField(verbose_name=_('Bicarbonate'), default=0, blank=False)
    sulfate = models.PositiveSmallIntegerField(verbose_name=_('Sulfate'), default=0, blank=False)
    chloride = models.PositiveSmallIntegerField(verbose_name=_('Chloride'), default=0, blank=False)
    sodium = models.PositiveSmallIntegerField(verbose_name=_('Sodium'), default=0, blank=False)
    magnesium = models.PositiveSmallIntegerField(verbose_name=_('Magnesium'), default=0, blank=False)
    ph = models.DecimalField(verbose_name=_('PH'), max_digits=3, decimal_places=1, default=0, blank=False)

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Water chemistry')
        verbose_name_plural = _('Water chemistry')
        abstract = True

    def __str__(self):
        return f'{_("Water chemistry")}'


class BeerStyleCategory(AbstractName):
    index = models.PositiveSmallIntegerField(verbose_name=_("Index"), blank=True, db_index=True)
    bjcp = models.PositiveSmallIntegerField(verbose_name=_("The year of publishing BJCP"), default=2015)  # Reserve
    guides = models.IntegerField(_("Beer Style Guidelines"), choices=BEER_STYLE_GUIDELINES, default=DEFAULT_GUIDES)

    class Meta:
        ordering = ['index', ]
        verbose_name = _('Beer Style Category')
        verbose_name_plural = _('Beer Style Categories')

    def __str__(self):
        return f'({self.guides}) {self.index}. {self.name}'


class BeerStyle(AbstractName):
    bjcp = models.PositiveSmallIntegerField(verbose_name=_("The year of publishing BJCP"), default=2015)  # Reserve
    guides = models.IntegerField(_("Beer Style Guidelines"), choices=BEER_STYLE_GUIDELINES, default=DEFAULT_GUIDES)
    type = models.IntegerField(_("Type beer"), choices=TYPE_BEER, default=SPECIAL_BEER)
    category = models.ForeignKey(BeerStyleCategory, verbose_name=_('Category'), null=True, blank=True,
                                 on_delete=models.PROTECT)
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
    SRM_min = models.DecimalField(verbose_name=_("SRM minimal"), max_digits=4, decimal_places=1)
    SRM_max = models.DecimalField(verbose_name=_("SRM maximal"), max_digits=4, decimal_places=1)
    CO2_min = models.DecimalField(verbose_name=_("Carbonisation min"), max_digits=2, decimal_places=1)
    CO2_max = models.DecimalField(verbose_name=_("Carbonisation max"), max_digits=2, decimal_places=1)

    class Meta:
        ordering = ['category', 'index']
        verbose_name = _('Beer Style')
        verbose_name_plural = _('Beer Styles')

    def __str__(self):
        return f'{self.index}. {self.name}'

    def get_absolute_url(self):
        return reverse('style_one', args=[self.slug])


class Country(AbstractName):
    pass

    class Meta:
        ordering = ['name',]
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')


class Company(AbstractName):
    pass

    class Meta:
        ordering = ['name',]
        verbose_name = _('Company')
        verbose_name_plural = _('Company')


class AbstractMade(models.Model):
    styles = models.ManyToManyField(BeerStyle, verbose_name=_('Use in styles'), blank=True)
    country = models.ForeignKey(Country, verbose_name=_('Country'), null=True, blank=True, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, verbose_name=_('Company'), null=True, blank=True, on_delete=models.PROTECT)
    url_source = models.URLField(verbose_name=_('Sourse'), null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        if self.company:
            return f'{self.name} - {self.company}'
        else:
            return f'{self.name}'


class Malt(AbstractName, AbstractMade):
    type = models.IntegerField(_("Type grain"), choices=TYPE_GRAIN, default=BASE_MALT)
    category = models.IntegerField(_("Category grain"), choices=MALT_CATEGORY, default=CATEGORY_BASE_MALT)
    share = models.PositiveSmallIntegerField(verbose_name=_("Share up in percentage"),
                                             help_text="0...100 %")
    color = models.DecimalField(verbose_name=_("Color in Lovibond"), max_digits=5, decimal_places=1,
                                blank=True, help_text="0...9999.9 \N{DEGREE SIGN}L")
    extractivity = models.DecimalField(verbose_name=_("Extractivity"), max_digits=3, decimal_places=1, blank=False,
                                       help_text="0...99.9 %")
    protein = models.DecimalField(verbose_name=_("Protein"), max_digits=3, decimal_places=1, null=True, blank=True,
                                  help_text="0...99.9 %")

    class Meta:
        ordering = ['type', 'name']
        verbose_name = _('Malt')
        verbose_name_plural = _('Malt')
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name='unique_malt')
        ]

    def get_absolute_url(self):
        return reverse('malt_one', args=[self.slug])


class Fermentable(AbstractName, AbstractMade):
    type = models.IntegerField(_("Type fermentable"), choices=TYPE_FERMENTABLE, default=SUGAR)
    color = models.DecimalField(verbose_name=_("Color in Lovibond"), max_digits=5, decimal_places=1,
                                blank=True, help_text="0...9999.9 \N{DEGREE SIGN}L")
    extractivity = models.DecimalField(verbose_name=_("Extractivity"), max_digits=3, decimal_places=1, blank=False,
                                       help_text="0...99.9 %")

    class Meta:
        ordering = ['type', 'name']
        verbose_name = _('Fermentable')
        verbose_name_plural = _('Fermentables')
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name='unique_ferm')
        ]

    def get_absolute_url(self):
        return reverse('ferm_one', args=[self.slug])


class Hops(AbstractName, AbstractMade):
    type = models.IntegerField(_("Type hops"), choices=TYPE_HOPS, default=PELLETS)
    alfa_acid = models.DecimalField(verbose_name=_("Alfa acid"), max_digits=3, decimal_places=1, blank=False,
                                    help_text="0...99.9 %")

    class Meta:
        ordering = ['name']
        verbose_name = _('Hop')
        verbose_name_plural = _('Hops')
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name='unique_hops')
        ]

    def get_absolute_url(self):
        return reverse('hop_one', args=[self.slug])


class Yeasts(AbstractName, AbstractMade):
    short_name = models.CharField(_("Short name"), max_length=20, blank=True, default='')
    type = models.IntegerField(_("Type yeast"), choices=TYPE_YEASTS, default=ALE)
    its_dry = models.BooleanField(verbose_name=_("It's dry yeast"), default=True, db_index=True)
    tolerance = models.DecimalField(verbose_name=_("Alcohol tolerance"), max_digits=3, decimal_places=1,
                                    null=True, blank=True, help_text="0...99.9 %")
    flocculation = models.IntegerField(_("Flocculation"), choices=FLOCCULATION, default=UNKNOWN)
    attenuation = models.DecimalField(verbose_name=_("Attenuation"), max_digits=3, decimal_places=1,
                                      blank=False, help_text="0...99.9 %")
    min_temperature = models.PositiveSmallIntegerField(verbose_name=_('Minimal temperature'), blank=False,
                                                       help_text="0...99 \N{DEGREE SIGN}C")
    max_temperature = models.PositiveSmallIntegerField(verbose_name=_('Maximal temperature'), blank=False,
                                                       help_text="0...99 \N{DEGREE SIGN}C")

    class Meta:
        ordering = ['name', 'type']
        verbose_name = _('Yeast')
        verbose_name_plural = _('Yeasts')
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name='unique_yeast')
        ]

    def get_absolute_url(self):
        return reverse('yeast_one', args=[self.slug])

    def __str__(self):
        if self.short_name:
            return f'{self.name} ({self.short_name})'
        else:
            return f'{self.name}'


class Misc(AbstractName, AbstractMade):
    type = models.IntegerField(_("Type additive"), choices=TYPE_ADDITIVE, default=SPICE)

    class Meta:
        ordering = ['name', 'type']
        verbose_name = _('Misc additive')
        verbose_name_plural = _('Misc additives')
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name='unique_misc')
        ]

    def get_absolute_url(self):
        return reverse('misc_one', args=[self.slug])


class WaterProfile(AbstractName, AbstractWater):
    styles = models.ManyToManyField(BeerStyle, verbose_name=_('Use in styles'), blank=True)

    class Meta:
        ordering = ['name', ]
        verbose_name = _('Water profile')
        verbose_name_plural = _('Water profiles')

    def get_absolute_url(self):
        return reverse('water_one', args=[self.slug])
