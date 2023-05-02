from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import BeerStyleCategory, BeerStyle, Country, Fermentable, \
                    Company, Malt, Hops, Misc, Yeasts, WaterProfile


@admin.register(BeerStyleCategory)
class BeerStyleCategoryAdmin(admin.ModelAdmin):
    list_display = ('index', 'name', 'guides')
    list_filter = ('index', 'name', 'guides')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main'), {'fields': [('index', 'name', 'slug', 'guides')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('description',)]}),
    )


class MaltInline(admin.TabularInline):
    model = Malt.styles.through


class HopsInline(admin.TabularInline):
    model = Hops.styles.through


class YeastsInline(admin.TabularInline):
    model = Yeasts.styles.through


@admin.register(BeerStyle)
class BeerStyleAdmin(admin.ModelAdmin):
    list_display = ('index', 'name', 'guides')
    list_filter = ('index', 'name', 'guides')
    inlines = [MaltInline, HopsInline, YeastsInline]
    fieldsets = (
        (_('Main'), {'fields': [('index', 'name', 'category'),
                                ('bjcp', 'type', 'guides')]}),
        (_('Vital Statistics'), {'fields': [('OG_min', 'OG_max', 'FG_min', 'FG_max'),
                                            ('ABV_min', 'ABV_max', 'IBUs_min', 'IBUs_max'),
                                            ('SRM_min', 'SRM_max', 'CO2_min', 'CO2_max')]}),
        (_('Description'), {'fields': [('description',), ('aroma',), ('appearance',), ('flavor',),
                                       ('mouthfeel',), ('comments',), ('history',), ('ingredients',),
                                       ('comparison')]}),
    )


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main'), {'fields': [('name', 'slug')]}),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main'), {'fields': [('name', 'slug')]}),
    )


@admin.register(Malt)
class MaltAdmin(admin.ModelAdmin):
    list_display = ('type', 'name', 'company', 'country')
    filter_horizontal = ('styles',)
    list_filter = ('type', 'name')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main'), {'fields': [('type', 'name', 'category', 'slug')]}),
        (_('Vital Statistics'), {'fields': [('extractivity', 'color', 'protein', 'share'),
                                            ('country', 'company')]}),
        (_('Description'), {'fields': [('description',),]}),
        (_('Use'), {'fields': [('styles',),]})

    )


@admin.register(Fermentable)
class FermentableAdmin(admin.ModelAdmin):
    list_display = ('name', 'type',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main'), {'fields': [('name', 'type', 'slug')]}),
        (_('Manufacturer'), {'fields': [('country', 'company')]}),
        (_('Parameters'), {'fields': [('color', 'extractivity')]}),
        (_('Description'), {'fields': [('description',),]})
    )


@admin.register(Hops)
class HopsAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'country')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('styles',)
    fieldsets = (
        (_('Main'), {'fields': [('name', 'slug')]}),
        (_('Manufacturer'), {'fields': [('country', 'company')]}),
        (_('Parameters'), {'fields': [('alfa_acid', 'type')]}),
        (_('Description'), {'fields': [('description',),]}),
        (_('Use'), {'fields': [('styles',), ]})
    )


@admin.register(Yeasts)
class YeastsAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'type', 'company', 'its_dry')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('styles',)
    fieldsets = (
        (_('Main'), {'fields': [('name', 'short_name', 'type', 'slug')]}),
        (_('Manufacturer'), {'fields': [('country', 'company')]}),
        (_('Parameters'), {'fields': [('its_dry', 'min_temperature', 'max_temperature'),
                                      ('tolerance', 'flocculation', 'attenuation')]}),
        (_('Description'), {'fields': [('description',),]}),
        (_('Use'), {'fields': [('styles',), ]})
    )


@admin.register(Misc)
class MiscAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main'), {'fields': [('name', 'type', 'slug')]}),
        (_('Description'), {'fields': [('description',),]})
    )


@admin.register(WaterProfile)
class WaterProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    fieldsets = (
        (_('Main'), {'fields': [('name', 'ph')]}),
        (_('Structure'), {'classes': ('collapse',),
                          'fields': [('calcum', 'bicarbonate', 'sulfate'),
                                     ('chloride', 'sodium', 'magnesium')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('description',)]}),
        (_('Use'), {'fields': [('styles',), ]})
    )