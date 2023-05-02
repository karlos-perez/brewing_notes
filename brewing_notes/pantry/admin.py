from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Pantry, MaltsReserve, HopsReserve, YeastsReserve, MaltsWriteOff, HopsWriteOff, YeastsWriteOff


@admin.register(MaltsReserve)
class MaltsReserveAdmin(admin.ModelAdmin):
    list_display = ('id', 'pantry', 'malt', 'spent', 'created_date')
    list_filter = ('pantry', 'malt', 'spent')
    fieldsets = (
        (_('Main'), {'fields': [('pantry', 'malt', 'created_date', 'expiration_date'),
                                ('parish', 'balance', 'cost_per_unit'),
                                ('spent', 'supplier')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('note',)]}),
    )


@admin.register(HopsReserve)
class HopsReserveAdmin(admin.ModelAdmin):
    list_display = ('id', 'pantry', 'hop', 'spent', 'created_date')
    list_filter = ('pantry', 'hop', 'spent')
    fieldsets = (
        (_('Main'), {'fields': [('pantry', 'hop', 'created_date', 'expiration_date'),
                                ('parish', 'balance', 'cost_per_unit'),
                                ('spent', 'supplier')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('note',)]}),
    )


@admin.register(YeastsReserve)
class YeastsReserveAdmin(admin.ModelAdmin):
    list_display = ('id', 'pantry', 'yeast', 'spent', 'created_date')
    list_filter = ('pantry', 'yeast', 'spent')
    fieldsets = (
        (_('Main'), {'fields': [('pantry', 'yeast', 'created_date', 'expiration_date'),
                                ('parish', 'balance', 'measure', 'cost_per_unit'),
                                ('spent', 'supplier')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('note',)]}),
    )


class MaltsReserveInline(admin.TabularInline):
    model = MaltsReserve
    extra = 1


class HopsReserveInline(admin.TabularInline):
    model = HopsReserve
    extra = 1


class YeastsReserveInline(admin.TabularInline):
    model = YeastsReserve
    extra = 1


@admin.register(Pantry)
class PantryAdmin(admin.ModelAdmin):
    inlines = [
        MaltsReserveInline,
        HopsReserveInline,
        YeastsReserveInline
    ]
    list_display = ('user', 'enabled')
    list_filter = ('enabled',)
    fieldsets = (
        (_('Main'), {'fields': [('user', 'enabled')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('description',)]}),
    )


@admin.register(MaltsWriteOff)
class MaltsWriteOffAdmin(admin.ModelAdmin):
    list_display = ('id', 'pantry', 'recipe', 'malt_reserve', 'amount')
    list_filter = ('pantry', 'recipe', 'malt_reserve')
    fieldsets = (
        (_('Main'), {'fields': [('pantry', 'recipe', 'malt_reserve'),
                                ('amount', 'cost', 'date')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('note',)]}),
    )


@admin.register(HopsWriteOff)
class HopsWriteOffAdmin(admin.ModelAdmin):
    list_display = ('id', 'pantry', 'recipe', 'hop_reserve', 'amount')
    list_filter = ('pantry', 'recipe', 'hop_reserve')
    fieldsets = (
        (_('Main'), {'fields': [('pantry', 'recipe', 'hop_reserve'),
                                ('amount', 'cost', 'date')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('note',)]}),
    )


@admin.register(YeastsWriteOff)
class YeastsWriteOffAdmin(admin.ModelAdmin):
    list_display = ('id', 'pantry', 'recipe', 'yeast_reserve', 'amount')
    list_filter = ('pantry', 'recipe', 'yeast_reserve')
    fieldsets = (
        (_('Main'), {'fields': [('pantry', 'recipe', 'yeast_reserve'),
                                ('amount', 'measure', 'cost', 'date')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('note',)]}),
    )