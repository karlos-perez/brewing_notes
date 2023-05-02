from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import BrewUser, Recipe, MashGuidelines, GrainIngredients, FermentableIngredients, \
    HopsIngredients, MiscIngredients, WaterTargetProfile, YeastsIngredients, Priming, \
    BrewingLog, EmailConfirmation, FermentationGuidelines, ConnectedDevice, \
    RecipeDataLog, UserTelegramProfile, WaterUserProfile, AccessKeyFullRecipe, \
    WaterOriginalProfile, WaterIngredient, EquipmentModules, Modules, VisitorData


@admin.register(BrewUser)
class BrewUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_confirm', 'is_active', 'is_banned', 'status', 'premium_end', 'premium_trial', 'is_staff', 'is_superuser', 'tester')
    fieldsets = (
        (None, {'fields': [('username',  'thumbnail', 'img'),]}),
        ("Profile", {"classes": ("grp-collapse grp-closed",), "fields": [('fullname', 'email'), ('signature',), ('about',)]}),
        ("Permission", {"classes": ("grp-collapse grp-closed",), "fields": [('is_confirm', 'is_active', 'editor', 'is_banned'),
                                                                            ('is_staff', 'is_superuser', 'tester'),
                                                                            ('premium_trial', 'status', 'premium_end')]}),
        ("Recipes", {"classes": ("grp-collapse grp-closed",), "fields": [('limit_draft',),
                                                                         ('recalc_recipes', 'recalc_on_size')]}),
        ("Devices", {"classes": ("grp-collapse grp-closed",), "fields": [('limit_device', 'limit_modules',),
                                                                         ('device_on_dashboard', 'records_limit')]}),
        ('System settings (!!!)', {"classes": ("grp-collapse grp-closed",), 'fields': [('last_login', 'date_joined'),
                                                                                       ('password',)]}),
    )
    readonly_fields = ('thumbnail', )
    list_filter = ('is_active', 'status')


@admin.register(AccessKeyFullRecipe)
class AccessKeyFullRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'access_key', 'created',)
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'access_key', 'created',),]}),
    )


@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'confirmation_key', 'sent',)
    fieldsets = (
        (_('Main'), {'fields': [('user', 'confirmation_key', 'sent',),]}),
    )


@admin.register(MashGuidelines)
class MashGuidelinesAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'type_rest', 'type_mash', 'step_temp', 'step_time')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'type_rest', 'type_mash', 'step_temp', 'step_time'),]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(GrainIngredients)
class GrainIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount', 'use')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ingredient', 'amount', 'use'),
                                ('dry_substance',)]}),
    )


@admin.register(FermentableIngredients)
class FermentableIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ingredient', 'amount', 'measure'),
                                ('use', 'time')]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(HopsIngredients)
class HopsIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount', 'use')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ingredient', 'alfa', 'amount'),
                                ('use', 'time')]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(MiscIngredients)
class MiscIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ingredient', 'amount', 'measure'),
                                ('use', 'time')]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(WaterTargetProfile)
class WaterTargetProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe',)
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ph'),
                                ('calcum', 'bicarbonate', 'sulfate',
                                 'chloride', 'sodium', 'magnesium')]}),
        (_('Note'), {'fields': [('note',)]}),
    )


@admin.register(WaterOriginalProfile)
class WaterOriginalProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe',)
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ph'),
                                ('calcum', 'bicarbonate', 'sulfate',
                                 'chloride', 'sodium', 'magnesium')]}),
        (_('Note'), {'fields': [('note',)]}),
    )


@admin.register(WaterIngredient)
class WaterIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe',)
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'additive'),
                                ('amount_mash', 'amount_sparge')]}),
        (_('Note'), {'fields': [('note',)]}),
    )


@admin.register(YeastsIngredients)
class YeastsIngredientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'ingredient', 'amount', 'measure'),]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(BrewingLog)
class BrewingLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'event', 'date')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'event', 'date'),]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(FermentationGuidelines)
class FermentationGuidelinesAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'temp', 'duration', 'stage')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'stage'),
                                ('temp', 'duration')]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


@admin.register(Priming)
class PrimingAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'priming_method', 'amount', 'measure', 'CO2_level')
    fieldsets = (
        (_('Main'), {'fields': [('recipe', 'priming_method', 'amount', 'measure'),
                                ('temp', 'CO2_level')]}),
        (_('Note'), {'classes': ('collapse',),
                     'fields': [('note',)]}),
    )


class MashGuidelinesInline(admin.TabularInline):
    model = MashGuidelines
    extra = 1


class GrainIngredientsInline(admin.TabularInline):
    model = GrainIngredients
    extra = 1


class FermentableIngredientsInline(admin.TabularInline):
    model = FermentableIngredients
    extra = 0


class HopsIngredientsInline(admin.TabularInline):
    model = HopsIngredients
    extra = 1


class MiscIngredientsInline(admin.TabularInline):
    model = MiscIngredients
    extra = 0


class WaterIngredientInline(admin.TabularInline):
    model = WaterIngredient
    extra = 0


class WaterTargetProfileInline(admin.TabularInline):
    model = WaterTargetProfile
    extra = 0


class WaterOriginalProfileInline(admin.TabularInline):
    model = WaterOriginalProfile
    extra = 0


class YeastsIngredientsInline(admin.TabularInline):
    model = YeastsIngredients
    extra = 1


class BrewingLogInline(admin.TabularInline):
    model = BrewingLog
    extra = 1


class FermentationGuidelinesInline(admin.TabularInline):
    model = FermentationGuidelines
    extra = 1


class PrimingInline(admin.TabularInline):
    model = Priming
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        MashGuidelinesInline,
        GrainIngredientsInline,
        FermentableIngredientsInline,
        HopsIngredientsInline,
        MiscIngredientsInline,
        WaterIngredientInline,
        WaterTargetProfileInline,
        WaterOriginalProfileInline,
        YeastsIngredientsInline,
        PrimingInline,
        FermentationGuidelinesInline,
        BrewingLogInline
    ]
    list_display = ('id', 'slug', 'name', 'user', 'style', 'created_date', 'public_date', 'status', 'enabled')
    readonly_fields = ['uid', 'slug', 'karma', 'created_date']
    list_filter = ('status', 'matches_style', 'сonformity')
    fieldsets = (
        (_('Main'), {'fields': [('name', 'user', 'private'),
                                ('uid', 'slug', 'karma', 'brew_number'),
                                ('type', 'style', 'cost'),
                                ('status', 'сonformity', 'matches_style'),
                                ('created_date', 'public_date'),
                                ('url_source', 'url_discussion'),
                                ('show_note', 'show_log', 'enabled'),
                                ('img')]}),
        (_('Recipe parametrs'), {'fields': [('abv', 'ibu', 'srm'),
                                            ('PBG', 'OG', 'FG'),
                                            ('efficiency_brew', 'efficiency_mash',)]}),
        (_('Brew parametrs'), {'fields': [('batch_size', 'mash_water', 'sparge_water', 'boil_time'),
                                          ('pre_boil_size', 'sediment_after_boil',
                                           'fermentation_size', 'starter_volume', 'bottling_size'),
                                          ('fermentation_temp', 'fermentation_duration', 'maturation',)]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('description',),
                                       ('note'),]}),
        (_('SEO'), {'classes': ('collapse',),
                    'fields': [('seo_title',),
                               ('seo_description',),
                               ('seo_keywords'),]}),
        (_('Favorites'), {'classes': ('collapse',),
                          'fields': [('favorites',),]}),
    )


@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'user', 'created_date', 'enabled', 'active', 'token')
    readonly_fields = ('token', 'created_date')
    fieldsets = (
        (_('Main'), {'fields': [('user', 'type', 'name'),
                                ('token', 'enabled', 'active'),
                                ('created_date', 'updated_date')]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('description',)]}),
    )


@admin.register(Modules)
class ModulesAdmin(admin.ModelAdmin):
    list_display = ('id',  'name', 'token', 'mode', 'user', 'created_date', 'enabled', 'active', )
    readonly_fields = ('token', 'created_date')
    list_filter = ('mode', 'user')
    fieldsets = (
        (_('Main'), {'fields': [('user', 'name', 'token'),
                                ('mode', 'enabled', 'active'),
                                ('created_date',)]}),
        (_('Description'), {'classes': ('collapse',),
                            'fields': [('description',)]}),
    )


@admin.register(EquipmentModules)
class EquipmentModulesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'user', 'active')
    fieldsets = (
        (_('Basic'), {'fields': [('user', 'type', 'name', 'active'),]}),
        (_('Main'), {'fields': [('main', 'hysteresys_m'),
                                ('kp_m', 'kd_m', 'ki_m')]}),
        (_('Second'), {'fields': [('second', 'hysteresys_s'),
                                  ('kp_s', 'kd_s', 'ki_s')]}),
        (_('Third'), {'fields': [('third', 'pump_init_cycle_t')]}),
        (_('Fourth'), {'fields': [('fourth', 'pump_init_cycle_f')]}),
    )


@admin.register(RecipeDataLog)
class RecipeDataLogAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'device', 'show_chart')
    fieldsets = (
        (_('Main'), {'fields': [('recipe',),
                                ('device', 'show_chart',)]}),
        (_('Data'), {'classes': ('collapse',),
                     'fields': [('data',)]}),
    )


@admin.register(UserTelegramProfile)
class UserTelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_tg_id', 'enabled', 'is_blocked_bot', 'is_banned', 'receive_notification')
    readonly_fields = ['created_date']
    fieldsets = (
        (_('Main'), {'fields': [('user', 'user_tg_id', 'language_code'),
                                ('username', 'first_name', 'last_name'),
                                ('enabled', 'deep_link'),
                                ('is_blocked_bot', 'is_banned', 'receive_notification'),
                                ('created_date', 'updated_date')]}),
    )

@admin.register(WaterUserProfile)
class WaterUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name')
    fieldsets = (
        (_('Main'), {'fields': [('user', 'name', 'slug'),
                                ('calcum', 'bicarbonate', 'sulfate'),
                                ('chloride', 'sodium', 'magnesium'),
                                ('ph',)]}),
        (_('Data'), {'classes': ('collapse',),
                     'fields': [('description',)]}),
    )


@admin.register(VisitorData)
class VisitorDataAdmin(admin.ModelAdmin):
    list_display = ('id',  'ip', 'user', 'date')
    readonly_fields = ('ip', 'date')
    list_filter = ('ip', 'user')
    fieldsets = (
        (_('Main'), {'fields': [('user', 'ip', 'date'),
                                ('user_agent')]}),
    )