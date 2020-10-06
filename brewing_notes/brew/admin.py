from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import BrewUser, BeerStyleCategory, BeerStyle, FermentablesCategory, Country, Company, Fermentables, Steps,\
                    Hops


@admin.register(BrewUser)
class BrewUserAdmin(UserAdmin):
    # list_display = ('username', 'email', 'is_active', 'date_joined')
    # list_filter = ('is_active',)
    # fieldsets = (
    #     (None, {'fields': [('username', 'is_staff', 'email'), ('thumbnail', 'img')]}),
    #     ("Profile", {"fields": [('fullname',), ('signature',), ('about',)]}),
    #     ('System settings (!!!)', {'fields': [('is_active', 'is_superuser'), ('last_login', 'date_joined'), ('password',)]}),
    # )
    # readonly_fields = ('thumbnail',)
    pass


@admin.register(BeerStyleCategory)
class BeerStyleCategoryAdmin(admin.ModelAdmin):
    list_display = ("index", "name",)
    prepopulated_fields = {"slug_name": ("name",)}
    fieldsets = (
        (_("Main"), {"fields": [("index", "name", "slug_name")]}),
        (_("Description"), {"classes": ("collapse",),
                            "fields": [("description",)]}),
    )


@admin.register(BeerStyle)
class BeerStyleAdmin(admin.ModelAdmin):
    list_display = ('index', "name")
    list_filter = ('index', "name")

    fieldsets = (
        (_("Main"), {"fields": [("index", "name", "category")]}),
        (_("Vital Statistics"), {"fields": [("OG_min", "OG_max", "FG_min", "FG_max"),
                                            ("ABV_min", "ABV_max", "IBUs_min", "IBUs_max"),
                                            ("SRM_min", "SRM_max")]}),
        (_("Description"), {"fields": [("description", "aroma", "appearance", "flavor", "mouthfeel", "comments",
                                        "history", "ingredients", "comparison"),]})
    )


@admin.register(FermentablesCategory)
class FermentablesCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    prepopulated_fields = {"slug_name": ("name",)}
    fieldsets = (
        (_("Main"), {"fields": [("name", "slug_name")]}),
        (_("Description"), {"classes": ("collapse",),
                            "fields": [("description",)]})
    )


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    prepopulated_fields = {"slug_name": ("name",)}
    fieldsets = (
        (_("Main"), {"fields": [("name", "slug_name")]}),
    )



@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    prepopulated_fields = {"slug_name": ("name",)}
    fieldsets = (
        (_("Main"), {"fields": [("name", "slug_name")]}),
    )


@admin.register(Fermentables)
class FermentablesAdmin(admin.ModelAdmin):
    list_display = ('category', 'name')
    list_filter = ('category', 'name')
    prepopulated_fields = {"slug_name": ("name",)}
    fieldsets = (
        (_("Main"), {"fields": [("category", "name", 'slug_name')]}),
        (_("Vital Statistics"), {"fields": [("extractivity", "color", "protein", "share"),
                                            ("country", "company")]}),
        (_("Description"), {"fields": [("description",),]})
    )


@admin.register(Steps)
class StepsAdmin(admin.ModelAdmin):
    list_display = ("name",)
    prepopulated_fields = {"slug_name": ("name",)}
    fieldsets = (
        (_("Main"), {"fields": [("name", "slug_name")]}),
    )
