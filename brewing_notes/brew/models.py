import datetime
import json
import hashlib
import logging
import random
import secrets
import uuid
from datetime import timedelta
from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db import models, IntegrityError
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from nnmware.core.abstract import AbstractName, AbstractDate, AbstractIP, PicsMixin
from nnmware.core.constants import STATUS_CHOICES, STATUS_DRAFT, STATUS_PUBLISHED, \
                                   STATUS_STICKY, STATUS_MODERATION, STATUS_LOCKED
from nnmware.core.managers import StatusManager
from nnmware.core.models import NnmwareUser, LikeMixin, ContentBlockMixin, Like

from catalog.constants import TYPE_BEER, SPECIAL_BEER, TYPE_GRAIN, TYPE_ADDITIVE, WATER_AGENT, ACIDS
from catalog.models import BeerStyle, Malt, Fermentable, Hops, Misc, Yeasts, AbstractWater

from .constants import (TYPE_REST, MASH_IN,
                        TYPE_HEATING, TEMPERATURE,
                        USE, USE_BOIL,
                        MEASURE, GRAM, KILOGRAM,
                        PRIMING_METHOD, CORN_SUGAR,
                        LOG_EVENT, LOG_BREW,
                        STATUS_CONFORMITY, CONFORMITY_NORMAL,
                        STATUS_USER, USER, PREMIUM, MODERATOR, PUNISHED, DUBIOUS, ENTITY,
                        ADMIN, TYPE_FERMENTATION, FERM_PRIMARY,
                        DEVICE_TYPE, DEVICE_BREWPILESS, DEVICE_ISPINDEL, WATER_ADDITIVE,
                        WATER_ADD_OTHER, EQUIPMENT_TYPE, MODULE_OPERATION_MODE,
                        MODULE_OM_NONE, EQUIPMENT_FERMENTER)
from .utils import get_uid, get_token


logger = logging.getLogger(__name__)


class SeoModel(models.Model):
    seo_title = models.CharField(_('Title SEO'), max_length=250, default='', blank=True)
    seo_description = models.CharField(_('Description SEO'), max_length=250, default='', blank=True)
    seo_keywords = models.CharField(_('Keywords SEO'), max_length=250, default='', blank=True)

    class Meta:
        abstract = True

    def get_seo_title(self):
        if self.seo_title:
            return self.seo_title
        return self.name

    def get_seo_description(self):
        if self.seo_description:
            return self.seo_description
        return self.name

    def get_seo_keywords(self):
        if self.seo_keywords:
            return self.seo_keywords
        return self.name


class AbstractDevice(AbstractName, AbstractDate):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.PROTECT)
    token = models.CharField(_('Token'), max_length=20, default='', unique=True)
    active = models.BooleanField(verbose_name=_("Active device"), default=False, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.token:
            try:
                self.token = get_token()
            except IntegrityError:
                self.token = get_token()
            self.save()


class ConnectedDevice(AbstractDevice, AbstractIP):
    type = models.IntegerField(_('Device type'), choices=DEVICE_TYPE, default=DEVICE_BREWPILESS)

    class Meta:
        ordering = ['name']
        verbose_name = _('Connected device')
        verbose_name_plural = _('Connected devices')

    def __str__(self):
        if self.name:
            return f'{self.name}'
        else:
            return f'{DEVICE_TYPE[self.type][1]}'

    @property
    def get_last_data(self):
        data = cache.get(str(self.token))
        if data is not None:
            return data
        else:
            return False


class Modules(AbstractDevice):
    mode = models.IntegerField(_('Operation mode'), choices=MODULE_OPERATION_MODE, default=MODULE_OM_NONE)

    class Meta:
        ordering = ['name']
        verbose_name = _('BNC-module')
        verbose_name_plural = _('BNC-modules')

    def __str__(self):
        if self.name:
            return f'{self.name}'
        else:
            return f'Module {self.id}'


class EquipmentModules(AbstractName):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.PROTECT)
    type = models.IntegerField(_('Type equipment'), choices=EQUIPMENT_TYPE, default=EQUIPMENT_FERMENTER)
    active = models.BooleanField(verbose_name=_("Active equipment"), default=False, db_index=True)
    main = models.OneToOneField(Modules, verbose_name=_('Main module'), on_delete=models.SET_NULL, null=True, blank=True, related_name='main')
    second = models.OneToOneField(Modules, verbose_name=_('Second module'), on_delete=models.SET_NULL, null=True, blank=True, related_name='second')
    third = models.OneToOneField(Modules, verbose_name=_('Third module'), on_delete=models.SET_NULL, null=True, blank=True, related_name='third')
    fourth = models.OneToOneField(Modules, verbose_name=_('Fourth module'), on_delete=models.SET_NULL, null=True, blank=True, related_name='fourth')
    kp_m = models.DecimalField(verbose_name=_('Kp main'), max_digits=3, decimal_places=1, default=1)
    kd_m = models.DecimalField(verbose_name=_('Kd main'), max_digits=3, decimal_places=1, default=0)
    ki_m = models.DecimalField(verbose_name=_('Ki main'), max_digits=3, decimal_places=1, default=0)
    hysteresys_m = models.DecimalField(verbose_name=_('Hysteresys main'), max_digits=3, decimal_places=1, default=0.5)
    kp_s = models.DecimalField(verbose_name=_('Kp second'), max_digits=3, decimal_places=1, default=1)
    kd_s = models.DecimalField(verbose_name=_('Kd second'), max_digits=3, decimal_places=1, default=0)
    ki_s = models.DecimalField(verbose_name=_('Ki second'), max_digits=3, decimal_places=1, default=0)
    hysteresys_s = models.DecimalField(verbose_name=_('Hysteresys second'), max_digits=3, decimal_places=1, default=0.5)
    pump_init_cycle_t = models.PositiveSmallIntegerField(verbose_name=_('Number of pump inits cycle third'), default=0)
    pump_init_cycle_f = models.PositiveSmallIntegerField(verbose_name=_('Number of pump inits cycle third'), default=0)

    class Meta:
        ordering = ['name']
        verbose_name = _('Equipment from modules')
        verbose_name_plural = _('Equipments from modules')
        constraints = [
            models.UniqueConstraint(fields=['main', 'second', 'third', 'fourth'], name='unique_equipment')
        ]

    def __str__(self):
        if self.name:
            return f'{self.name}'
        else:
            return f'{EQUIPMENT_TYPE[self.type][1]}'

    @property
    def is_ready(self):
        tp = self.type
        result = False
        if tp == 0:  # Fermenter
            if self.main and not self.third and not self.fourth:
                result = True
        elif tp == 1:  # Kettle
            if self.main and not self.second and not self.third and not self.fourth:
                result = True
        elif tp in (2, 3):  # BIAB & K-RIMS tt
            if self.main and not self.second and self.third and not self.fourth:
                result = True
        elif tp == 4:  # K-RIMS sl
            if self.main and not self.second and self.third and self.fourth:
                result = True
        return result


class BrewUser(NnmwareUser, LikeMixin, PicsMixin):
    status = models.IntegerField(_('Status user'), choices=STATUS_USER, default=USER)
    limit_draft = models.PositiveSmallIntegerField(verbose_name=_('Recipe draft limit'), default=5)
    limit_device = models.PositiveSmallIntegerField(verbose_name=_('Device connected limit'), default=2)
    limit_modules = models.PositiveSmallIntegerField(verbose_name=_('BNC-module limit'), default=4)
    limit_equipment = models.PositiveSmallIntegerField(verbose_name=_('Equipment limit'), default=4)
    is_active = models.BooleanField(verbose_name=_('Active'), default=False)
    is_confirm = models.BooleanField(verbose_name=_('Confirm'), default=False)
    editor = models.BooleanField(verbose_name=_('May add ingredients'), default=False)
    tester = models.BooleanField(verbose_name=_('Early release access'), default=False)
    is_banned = models.BooleanField(verbose_name=_('Eternal ban'), default=False)
    premium_trial = models.BooleanField(verbose_name=_('Can premium trial'), default=True)
    premium_end = models.DateField(verbose_name=_('Premium expiration date'), null=True, blank=True)
    records_limit = models.PositiveSmallIntegerField(verbose_name=_('Limit the log records in days'), default=30)
    device_on_dashboard = models.OneToOneField(ConnectedDevice, verbose_name=_('Device on dashboard'), null=True,
                                               blank=True, on_delete=models.CASCADE)
    recalc_recipes = models.BooleanField(verbose_name=_('Recalculate recipes'), default=False)
    recalc_on_size = models.DecimalField(verbose_name=_('Recalculate on new size'), max_digits=4, decimal_places=1,
                                         default=0)

    @property
    def is_editor(self):
        if self.editor and self.is_pro or self.is_admin:
            return True
        else:
            return False

    @property
    def is_tester(self):
        if self.tester and self.is_pro or self.is_admin:
            return True
        else:
            return False

    @property
    def recipe_count(self):
        qq = Q(status=STATUS_PUBLISHED) | Q(status=STATUS_STICKY) |\
             Q(status=STATUS_DRAFT) | Q(status=STATUS_MODERATION)
        rcp = Recipe.objects.filter(user=self)
        recipe = rcp.filter(qq).count()
        return recipe

    @property
    def all_recipes(self):
        qq = Q(status=STATUS_PUBLISHED) | Q(status=STATUS_STICKY) |\
             Q(status=STATUS_DRAFT) | Q(status=STATUS_MODERATION)
        return self.recipe_set.filter(qq).order_by('-created_date')

    @property
    def recipe_draft(self):
        recipe = Recipe.objects.filter(user=self, status=STATUS_DRAFT)
        return recipe

    @property
    def recipe_draft_count(self):
        return self.recipe_draft.count()

    @property
    def recipe_publish_count(self):
        recipe = Recipe.objects.filter(user=self, status=STATUS_PUBLISHED).count()
        return recipe

    @property
    def ability_to_add(self):  #TODO: переименовать в recipe ability to add
        draft = self.recipe_draft_count
        if draft >= self.limit_draft and self.status < ADMIN:
            return False
        else:
            return True

    @property
    def all_device(self):
        return ConnectedDevice.objects.filter(user=self, enabled=True)

    @property
    def all_bnc_modules(self):
        return Modules.objects.filter(user=self, enabled=True)

    @property
    def all_equipment(self):
        return EquipmentModules.objects.filter(user=self, enabled=True)

    @property
    def device_available(self):
        if not self.is_pro:
            return False
        dev = self.all_device.count()
        if dev >= self.limit_device and self.status < ADMIN:
            return False
        else:
            return True

    @property
    def module_available(self):
        if not self.is_pro:
            return False
        mod = self.all_bnc_modules.count()
        if mod >= self.limit_modules and self.status < ADMIN:
            return False
        else:
            return True

    @property
    def equipment_available(self):
        if not self.is_pro:
            return False
        equp = self.all_equipment.count()
        if equp >= self.limit_equipment and self.status < ADMIN:
            return False
        else:
            return True

    @property
    def ability_to_add_water(self):  #TODO: переименовать в watersource ability to add
        wp = self.wateruserprofile_set.all()
        if wp.count() > settings.LIMIT_USERS_WATER_PROFILE and self.status < ADMIN:
            return False
        else:
            return True

    @property
    def is_pro(self):
        if self.status >= PREMIUM:
            return True
        else:
            return False

    @property
    def is_moderator(self):
        if self.status >= MODERATOR:
            return True
        else:
            return False

    @property
    def is_admin(self):
        if self.status >= ADMIN:
            return True
        else:
            return False

    @property
    def available_telegram(self):
        if hasattr(self, 'usertelegramprofile'):
            if self.usertelegramprofile.enabled and not self.usertelegramprofile.is_blocked_bot and\
               not self.usertelegramprofile.is_banned:
                return True
        return False

    @property
    def available_pantry(self):
        if hasattr(self, 'pantry'):
            if self.pantry.enabled and self.is_pro:
                return True
        return False

    @property
    def get_logo(self):
        try:
            return self.allpics[0].img.url
        except:
            return settings.DEFAULT_LOGO

    def save(self, *args, **kwargs):
        self.date_modified = now()
        super().save(*args, **kwargs)
        if not self.is_active and not self.is_banned:
            c = EmailConfirmation.objects.filter(user=self.id)
            if not c:
                EmailConfirmation.objects.send_confirm_email(self)


class EmailConfirmationManager(models.Manager):
    def send_confirm_email(self, user):
        confirmation_key = hashlib.sha256((str(random.random())+user.email).encode('utf-8')).hexdigest()[:40]
        try:
            curr_site = Site.objects.get_current()
        except Site.DoesNotExist:
            return
        email_subject = _('Confirmation of registration at the {}').format(curr_site.name)
        path = reverse('confirmation', kwargs={'confirm_key': confirmation_key})
        activate_url = f'https://{curr_site.domain}{path}'
        ctx = {
            'user': user,
            'activate_url': activate_url,
        }
        email_body = render_to_string('registration/confirmation_email.txt', ctx)
        try:
            msg = EmailMessage(email_subject, email_body, to=[user.email])
            msg.send()
        except Exception as err:
            logger.error(f'Send Email Confirmation error: {err}')
        return self.create(
            user=user,
            confirmation_key=confirmation_key,
            sent=now())

    def confirmation(self, key):
        try:
            confirmation = self.get(confirmation_key=key)
        except self.model.DoesNotExist:
            return None
        user = confirmation.user
        ## todo пересмотреть
        if user.is_banned or user.is_confirm:
            return None
        if not confirmation.expire_dt():
            user.is_confirm = True
            user.is_active = True
            user.save()
            return user
        else:
            return None


class EmailConfirmation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.CASCADE)
    confirmation_key = models.CharField(verbose_name=_('Confirmation key'), max_length=40, db_index=True)
    sent = models.DateTimeField()

    objects = EmailConfirmationManager()

    class Meta:
        verbose_name = _('Email confirmation')
        verbose_name_plural = _('Email confirmations')

    def __str__(self):
        return f'Confirmation for {self.user}'

    def expire_dt(self):
        expired = self.sent + datetime.timedelta(days=settings.EMAIL_CONFIRMATION_DAYS)
        return now() >= expired


# class ProfileUser(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.CASCADE)


class WaterUserProfile(AbstractWater):
    user = models.ForeignKey(BrewUser, verbose_name=_('User'), on_delete=models.PROTECT)
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True, db_index=True, default='')
    description = models.TextField(verbose_name=_("Description"), blank=True, default='')

    class Meta:
        ordering = ['user', 'name']
        verbose_name = _('User water profile')
        verbose_name_plural = _('User water profiles')

    def __str__(self):
        return f'{_("User water profile")} {self.name}'
    #
    # def save(self, *args, **kwargs):
    #     if not self.slug:
    #         if not self.id:
    #             super().save(*args, **kwargs)
    #         self.slug = self.id
    #     else:
    #         self.slug = str(self.slug).strip().replace(' ', '-')
    #     super().save(*args, **kwargs)


class Recipe(AbstractName, AbstractDate, LikeMixin, ContentBlockMixin, AbstractIP, SeoModel, PicsMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.PROTECT)
    type = models.IntegerField(_('Type beer'), choices=TYPE_BEER, default=SPECIAL_BEER)
    style = models.ForeignKey(BeerStyle, verbose_name=_('Beer Style'), null=True,
                              blank=True, on_delete=models.PROTECT)
    batch_size = models.DecimalField(verbose_name=_('Batch size (after boil)'), max_digits=4, decimal_places=1, default=0)
    mash_water = models.DecimalField(verbose_name=_('Mash water'), max_digits=4, decimal_places=1, default=0)
    sparge_water = models.DecimalField(verbose_name=_('Sparge water'), max_digits=4, decimal_places=1, default=0)
    pre_boil_size = models.DecimalField(verbose_name=_('Volume after mash (pre boil)'), max_digits=4, decimal_places=1, default=0)
    sediment_after_boil = models.DecimalField(verbose_name=_('Sediment after boil'), max_digits=4, decimal_places=1, default=0)
    fermentation_size = models.DecimalField(verbose_name=_('Volume in fermenter'), max_digits=4, decimal_places=1, default=0)  # убрал в резерв
    bottling_size = models.DecimalField(verbose_name=_('Bottling size'), max_digits=4, decimal_places=1, default=0)
    starter_volume = models.DecimalField(verbose_name=_('Yeast starter volume'), max_digits=4, decimal_places=1, default=0)
    boil_time = models.PositiveSmallIntegerField(verbose_name=_('Boil time'), default=60)
    efficiency_brew = models.DecimalField(verbose_name=_('Efficiency brewing'), max_digits=3, decimal_places=1, default=0)
    efficiency_mash = models.DecimalField(verbose_name=_('Efficiency mashing'), max_digits=3, decimal_places=1, default=0)  # reserve
    PBG = models.DecimalField(verbose_name=_('Pre boil gravity'), max_digits=4, decimal_places=3, default=1.000)
    OG = models.DecimalField(verbose_name=_('Original gravity'), max_digits=4, decimal_places=3, default=1.000)
    FG = models.DecimalField(verbose_name=_('Final gravity'), max_digits=4, decimal_places=3, default=1.000)
    abv = models.DecimalField(verbose_name=_('Alcohol'), max_digits=3, decimal_places=1, default=0)
    ibu = models.PositiveSmallIntegerField(verbose_name=_('IBUs'), default=0)
    srm = models.DecimalField(verbose_name=_('Color in SRM'), max_digits=4, decimal_places=1, default=0)
    сonformity = models.IntegerField(_('Conformity'), choices=STATUS_CONFORMITY, default=CONFORMITY_NORMAL)
    maturation = models.PositiveSmallIntegerField(verbose_name=_('Maturation time'), null=True, blank=True)  # убрал в резерв
    uid = models.CharField(verbose_name=_("UID"), max_length=255, blank=True, db_index=True, default='')
    status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_DRAFT)
    fermentation_temp = models.PositiveSmallIntegerField(verbose_name=_('Fermentation temperature'), default=0)  # убрал в резерв
    fermentation_duration = models.PositiveSmallIntegerField(verbose_name=_('Fermentation duration'), default=0)  # убрал в резерв
    note = models.TextField(verbose_name=_('Note'), blank=True, default='')
    show_salts = models.BooleanField(verbose_name=_('Water agent'), default=False)
    show_note = models.BooleanField(verbose_name=_('Show note'), default=True)
    show_log = models.BooleanField(verbose_name=_('Show log'), default=True)
    matches_style = models.BooleanField(verbose_name=_('Matches the style'), default=False)
    cost = models.DecimalField(verbose_name=_('Cost recipe'), null=True, max_digits=7, decimal_places=2, blank=True)
    url_source = models.URLField(verbose_name=_('Recipe source'), null=True, blank=True)
    url_discussion = models.URLField(verbose_name=_('Discussion of the recipe'), null=True, blank=True)
    favorites = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='favorites', blank=True)
    slug = models.UUIDField(verbose_name=_('URL-identifier'), db_index=True, default=uuid.uuid4, unique=True, editable=False)
    public_date = models.DateTimeField(verbose_name=_("Publication date"), null=True, blank=True)
    private = models.BooleanField(verbose_name=_('Private recipe'), default=False)
    brew_number = models.PositiveIntegerField(verbose_name=_('Brew number'), default=0)

    objects = StatusManager()

    _copied_relationship = ['mashguidelines_set', 'grainingredients_set', 'fermentableingredients_set',
                            'hopsingredients_set', 'miscingredients_set', 'yeastsingredients_set', 'priming']

    class Meta:
        ordering = ['-created_date', ]
        verbose_name = _('Beer recipe')
        verbose_name_plural = _('Beer recipes')

    def __str__(self):
        return f'{self.id}.{self.name}'

    def get_short_url(self):
        if not self.uid:
            self.uid = get_uid(self.pk)
            self.save()
        return reverse('recipes_print_lite', args=[self.uid])

    def get_full_short_link(self):
        short = self.get_short_url()
        curr_site = Site.objects.get_current()
        return f'https://{curr_site.domain}{short}'

    def get_absolute_url(self):
        return reverse('recipe_detail', args=[self.slug])

    def get_temp_full_link(self):
        try:
            key = AccessKeyFullRecipe.objects.get(recipe=self)
        except ObjectDoesNotExist:
            return None
        if not key.expire_dt():
            # curr_site = Site.objects.get_current()
            # return f"https://{curr_site.domain}{reverse('recipe_temp_full', args=[key.access_key])}"
            return reverse('recipe_temp_full', args=[key.access_key])
        else:
            key.delete()
            return None

    def create_temp_full_link(self):
        try:
            ck = AccessKeyFullRecipe.objects.get(recipe=self)
            ck.delete()
        except ObjectDoesNotExist:
            pass
        key = secrets.token_urlsafe()
        AccessKeyFullRecipe.objects.create(recipe=self,
                                           access_key=key,
                                           created=now())
        return reverse('recipe_temp_full', args=[key])

    @property
    def copy_increment(self):
        if self.views is None:
            self.views = 1
        else:
            self.views += 1
        self.save()

    def create_copy(self, user, recalc):
        """
        Making a copy of a recipe
        recalc - batch size conversion factor
        """
        if user.is_pro:
            self._copied_relationship.append('watertargetprofile')
        attrs = {}
        for rs in self._copied_relationship:
            att = getattr(self, rs, None)
            if att is not None:
                if rs.endswith('_set'):
                    if rs == 'miscingredients_set':
                        attrs[rs] = att.exclude(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))
                    else:
                        attrs[rs] = att.all()
                else:
                    attrs[rs] = att
        if self.user != user:
            self.copy_increment
        new = self
        new.pk = None
        new.user = user
        new.uid = ''
        new.сonformity = CONFORMITY_NORMAL
        new.img = ''
        new.url_discussion = ''
        new.status = STATUS_DRAFT
        new.slug = uuid.uuid4()
        new.name = f'Copy: {self.name}'
        new.karma = 0
        new.views = 0
        new.batch_size = round(float(self.batch_size) * recalc, 1)
        new.mash_water = round(float(self.mash_water) * recalc, 1)
        new.sparge_water = round(float(self.sparge_water) * recalc, 1)
        new.note = ''
        new.description = ''
        new.created_date = now()
        new.public_date = None
        if user.is_pro:
            new.pre_boil_size = round(float(self.pre_boil_size) * recalc, 1)
            new.fermentation_size = round(float(self.fermentation_size) * recalc, 1)
            new.bottling_size = round(float(self.bottling_size) * recalc, 1)
        else:
            new.PBG = 1.0
            new.pre_boil_size = 0
            new.fermentation_size = 0
            new.bottling_size = 0
            new.sediment_after_boil = 0
            new.starter_volume = 0
            new.efficiency_mash = 0
            new.maturation = 0
        new.save()
        for attr in attrs.keys():
            if attr.endswith('_set'):
                for i in attrs.get(attr):
                    i.pk = None
                    amt = getattr(i, 'amount', None)
                    if amt is not None:
                        i.amount = round(float(amt) * recalc, 1)
                    i.save()
                    at = getattr(new, attr)
                    at.add(i)
            else:
                j = attrs.get(attr)
                j.pk = None
                j.recipe = new
                j.save()
        new.url_source = self.get_full_short_link()
        new.save()
        return new

    def __style_check(self):
        result = False
        if self.OG and self.FG and self.abv and self.ibu and self.srm:
            st = self.style
            if st.OG_min <= self.OG <= st.OG_max and st.FG_min <= self.FG <= st.FG_max and \
               st.ABV_min <= self.abv <= st.ABV_max and st.IBUs_min <= self.ibu <= st.IBUs_max and \
               st.SRM_min <= self.srm <= st.SRM_max:
                result = True
        return result

    def save(self, *args, **kwargs):
        if self.style:
            st = BeerStyle.objects.get(pk=self.style.pk)
            self.type = st.type
        else:
            self.type = SPECIAL_BEER
        if self.views is None:
            self.views = 0
        if self.status == STATUS_DRAFT:
            self.matches_style = self.__style_check()
        super().save(*args, **kwargs)
        if not self.uid:
            self.uid = get_uid(self.pk)
            self.save()
        # if self.status == STATUS_DRAFT:
        #     self.matches_style = self.__style_check()
        #     self.save()

    @property
    def get_list_ingredients(self):
        recipe = self
        ingredients = dict()
        misc = recipe.miscingredients_set.exclude(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))
        addition = list(chain(recipe.fermentableingredients_set.all(),
                              misc,))
        for i in recipe.grainingredients_set.all().order_by('-amount'):
            if i.ingredient.name in ingredients.keys():
                ingredients[i.ingredient.name]['amount'] += i.amount
            else:
                ingredients[i.ingredient.name] = {'amount': i.amount,
                                                  'measure': MEASURE[KILOGRAM][1],
                                                  'type': TYPE_GRAIN[i.ingredient.type][1],
                                                  'name': f'{i.ingredient.name} ({i.ingredient.company})',
                                                  'url': f'{i.ingredient.get_absolute_url()}'}
        for i in recipe.hopsingredients_set.all().order_by('ingredient__name'):
            if i.ingredient.name in ingredients.keys():
                ingredients[i.ingredient.name]['amount'] += i.amount
            else:
                ingredients[i.ingredient.name] = {'amount': i.amount,
                                                  'measure': MEASURE[GRAM][1],
                                                  'type': i.ingredient._meta.verbose_name,
                                                  'name': f'{i.ingredient.name} ({i.ingredient.company})',
                                                  'url': f'{i.ingredient.get_absolute_url()}'}
        for i in recipe.yeastsingredients_set.all():
            if i.ingredient.name in ingredients.keys():
                ingredients[i.ingredient.name]['amount'] += i.amount
            else:
                ingredients[i.ingredient.name] = {'amount': i.amount,
                                                  'measure': MEASURE[i.measure][1],
                                                  'type': i.ingredient._meta.verbose_name,
                                                  'name': f'{i.ingredient.name} ({i.ingredient.company})',
                                                  'url': f'{i.ingredient.get_absolute_url()}'}
        for i in addition:
            if i.ingredient.name in ingredients.keys():
                ingredients[i.ingredient.name]['amount'] += i.amount
            else:
                ingredients[i.ingredient.name] = {'amount': i.amount,
                                                  'measure': MEASURE[i.measure][1],
                                                  'type': TYPE_ADDITIVE[i.ingredient.type][1],
                                                  'name': f'{i.ingredient.name} ({i.ingredient.company})',
                                                  'url': f'{i.ingredient.get_absolute_url()}'}
        return ingredients


class AbstractIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, verbose_name=_('Recipe'), on_delete=models.CASCADE)
    note = models.TextField(verbose_name=_('Note'), blank=True, default='')

    class Meta:
        abstract = True


class MashGuidelines(AbstractIngredients):
    type_rest = models.IntegerField(_('Type rest'), choices=TYPE_REST, default=MASH_IN)
    type_mash = models.IntegerField(_('Type heating'), choices=TYPE_HEATING, default=TEMPERATURE)
    step_temp = models.PositiveSmallIntegerField(verbose_name=_('Mash temperature'), default=0, blank=False)
    step_time = models.PositiveSmallIntegerField(verbose_name=_('Holding time'), default=30, blank=False)

    class Meta:
        ordering = ['pk', 'step_temp',]
        verbose_name = _('Mash Step')
        verbose_name_plural = _('Mash Steps')

    def __str__(self):
        return f'{self.type_rest}'


class GrainIngredients(AbstractIngredients):
    ingredient = models.ForeignKey(Malt, verbose_name=_('Grain ingredient'), on_delete=models.PROTECT)
    amount = models.DecimalField(verbose_name=_('Amount in kg'), max_digits=5, decimal_places=2, default=0, blank=False)
    use = models.IntegerField(_("Grain"), choices=TYPE_REST, default=MASH_IN)
    dry_substance = models.DecimalField(verbose_name=_('Dry substance'), max_digits=5, decimal_places=2, default=0, blank=True)
    cost = models.DecimalField(verbose_name=_('Cost ingredient'), null=True, max_digits=7, decimal_places=2, blank=True)

    # При сохранении расчитывать массу сухого вещества
    class Meta:
        ordering = ['recipe', ]
        verbose_name = _('Grain ingredient')
        verbose_name_plural = _('Grain ingredients')

    def __str__(self):
        return f'{self.ingredient}'


class FermentableIngredients(AbstractIngredients):
    ingredient = models.ForeignKey(Fermentable, verbose_name=_('Fermentable ingredient'), null=True,
                                   blank=True, on_delete=models.PROTECT)
    amount = models.DecimalField(verbose_name=_('Amount'), max_digits=5, decimal_places=2, default=0, blank=True)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)
    use = models.IntegerField(_('When use'), choices=USE, default=USE_BOIL)
    time = models.PositiveSmallIntegerField(verbose_name=_('Time addition'), default=0, blank=True)
    cost = models.DecimalField(verbose_name=_('Cost ingredient'), null=True, max_digits=7, decimal_places=2, blank=True)

    class Meta:
        ordering = ['recipe', ]
        verbose_name = _('Fermentable ingredient')
        verbose_name_plural = _('Fermentable ingredients')

    def __str__(self):
        return f'{self.ingredient}'


class HopsIngredients(AbstractIngredients):
    ingredient = models.ForeignKey(Hops, verbose_name=_('Hops'), on_delete=models.PROTECT)
    amount = models.PositiveIntegerField(verbose_name=_("Amount in gram"), default=0, blank=False)
    use = models.IntegerField(_('When use'), choices=USE, default=USE_BOIL)
    time = models.PositiveSmallIntegerField(verbose_name=_('Time addition'), blank=False, default=60)
    alfa = models.DecimalField(verbose_name=_('Alfa acid'), max_digits=3, decimal_places=1, default=0)
    temp = models.PositiveSmallIntegerField(verbose_name=_('Temperature Hop Stand'), null=True, blank=True)
    cost = models.DecimalField(verbose_name=_('Cost ingredient'), null=True, max_digits=7, decimal_places=2, blank=True)

    class Meta:
        ordering = ['recipe', '-time']
        verbose_name = _('Hops ingredient')
        verbose_name_plural = _('Hops ingredients')

    def __str__(self):
        return f'{self.ingredient}'


class MiscIngredients(AbstractIngredients):
    ingredient = models.ForeignKey(Misc, verbose_name=_('Misc ingredient'), null=True,
                                   blank=True, on_delete=models.PROTECT)
    amount = models.DecimalField(verbose_name=_('Amount'), max_digits=5, decimal_places=2, default=0, blank=False)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)
    use = models.IntegerField(_('When use'), choices=USE, default=USE_BOIL)
    time = models.PositiveSmallIntegerField(verbose_name=_('Time addition'), default=0, blank=True)
    cost = models.DecimalField(verbose_name=_('Cost ingredient'), null=True, max_digits=7, decimal_places=2, blank=True)

    class Meta:
        ordering = ['recipe', ]
        verbose_name = _('Misc ingredient')
        verbose_name_plural = _('Misc ingredients')

    def __str__(self):
        return f'{self.ingredient}'


class YeastsIngredients(AbstractIngredients):
    ingredient = models.ForeignKey(Yeasts, verbose_name=_('Yeast'), on_delete=models.PROTECT)
    amount = models.DecimalField(verbose_name=_('Amount'), max_digits=5, decimal_places=2, default=0, blank=False)
    measure = models.IntegerField(_('Measure'), choices=MEASURE, default=GRAM)
    cost = models.DecimalField(verbose_name=_('Cost ingredient'), null=True, max_digits=7, decimal_places=2, blank=True)

    class Meta:
        ordering = ['recipe', 'ingredient']
        verbose_name = _('Yeasts ingredient')
        verbose_name_plural = _('Yeasts ingredients')

    def __str__(self):
        return f'{self.ingredient}'


class Priming(AbstractIngredients):
    recipe = models.OneToOneField(Recipe, verbose_name=_('Recipe'), on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=5, decimal_places=2, default=0)
    measure = models.IntegerField(_("Measure"), choices=MEASURE, default=GRAM)
    temp = models.PositiveSmallIntegerField(verbose_name=_('Temperature'), null=True, blank=True)
    priming_method = models.IntegerField(_("Priming method"), choices=PRIMING_METHOD, default=CORN_SUGAR)
    CO2_level = models.DecimalField(verbose_name=_("Carbonisation level"), max_digits=2, decimal_places=1, default=0, blank=True)
    cost = models.DecimalField(verbose_name=_("Cost ingredient"), null=True, max_digits=7, decimal_places=2, blank=True)

    class Meta:
        ordering = ['recipe', ]
        verbose_name = _('Priming Information')
        verbose_name_plural = _('Priming Information')

    def __str__(self):
        return f'{_("Priming Information")}'


class WaterTargetProfile(AbstractWater, AbstractIngredients):
    recipe = models.OneToOneField(Recipe, verbose_name=_('Recipe'), on_delete=models.CASCADE)

    class Meta:
        ordering = ['recipe', ]
        verbose_name = _('Water target profile')
        verbose_name_plural = _('Water target profiles')

    def __str__(self):
        return f'{_("Water target profile")}'


class WaterOriginalProfile(AbstractWater, AbstractIngredients):
    recipe = models.OneToOneField(Recipe, verbose_name=_('Recipe'), on_delete=models.CASCADE)

    class Meta:
        ordering = ['recipe',]
        verbose_name = _('Water original profile')
        verbose_name_plural = _('Water original profiles')

    def __str__(self):
        return f'{_("Water original profile")}'


class WaterIngredient(AbstractIngredients):
    additive = models.IntegerField(_('Additive'), choices=WATER_ADDITIVE, default=WATER_ADD_OTHER)
    amount_mash = models.DecimalField(verbose_name=_("Amount in mash water"), max_digits=7, decimal_places=1, default=0)
    amount_sparge = models.DecimalField(verbose_name=_("Amount in sparge water"), max_digits=7, decimal_places=1, default=0)

    class Meta:
        ordering = ['recipe', 'additive']
        verbose_name = _('Additive to water')
        verbose_name_plural = _('Additives to water')

    def __str__(self):
        return f'{_("Additives to water")}'


class BrewingLog(AbstractIngredients):
    event = models.IntegerField(_('Event'), choices=LOG_EVENT, default=LOG_BREW)
    date = models.DateField(verbose_name=_('Date event'), auto_now=False, auto_now_add=False, null=True, blank=True)

    class Meta:
        ordering = ['recipe', ]
        verbose_name = _('Brewing log')
        verbose_name_plural = _('Brewing logs')

    def __str__(self):
        return f'{_("Brewing log")}'


class FermentationGuidelines(AbstractIngredients):
    stage = models.IntegerField(_('Stage fermentation'), choices=TYPE_FERMENTATION, default=FERM_PRIMARY)
    temp = models.PositiveSmallIntegerField(verbose_name=_('Temperature fermentation'), default=17)
    duration = models.PositiveSmallIntegerField(verbose_name=_('Duration in days'), default=14)
    order = models.PositiveSmallIntegerField(verbose_name=_('Order'), default=1, blank=True)

    class Meta:
        ordering = ['recipe', 'order']
        verbose_name = _('Fermentation guideline')
        verbose_name_plural = _('Fermentation guidelines')

    def __str__(self):
        return f'{_("Fermentation guideline")}'


class RecipeDataLog(models.Model):
    recipe = models.OneToOneField(Recipe, verbose_name=_('Recipe'), on_delete=models.CASCADE)
    device = models.IntegerField(_('Device type'), choices=DEVICE_TYPE, default=DEVICE_BREWPILESS)
    show_chart = models.BooleanField(verbose_name=_('Show chart'), default=True)
    data = models.JSONField(verbose_name=_('Chart data'))

    class Meta:
        ordering = ['recipe']
        verbose_name = _('Recipe chart data')
        verbose_name_plural = _('Recipe chart data')


class UserTelegramProfile(AbstractDate):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.CASCADE)
    user_tg_id = models.IntegerField(verbose_name=_('User ID in Telegram'), unique=True, db_index=True)
    username = models.CharField(verbose_name=_('Username in TG'), max_length=32, default='')
    first_name = models.CharField(verbose_name=_('First name in TG'), max_length=256, default='')
    last_name = models.CharField(verbose_name=_('Last name in TG'), max_length=256, default='')
    language_code = models.CharField(verbose_name=_('Telegram client lang'), max_length=8, default='')
    deep_link = models.CharField(verbose_name=_('User deeplink'), max_length=64, default='')
    enabled = models.BooleanField(verbose_name=_('Profile enabled'), default=True)
    is_blocked_bot = models.BooleanField(verbose_name=_('User blocked bot'), default=False)
    is_banned = models.BooleanField(verbose_name=_('User banned'), default=False)
    receive_notification = models.BooleanField(verbose_name=_('Receive notification'), default=True)

    class Meta:
        ordering = ['user']
        verbose_name = _('User Telegram profile')
        verbose_name_plural = _('Users Telegram profiles')

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @property
    def can_receive_message(self):
        if not self.is_blocked_bot and not self.is_banned and self.receive_notification:
            return True
        else:
            return False


class AccessKeyFullRecipe(models.Model):
    recipe = models.OneToOneField(Recipe, verbose_name=_('Recipe'), on_delete=models.CASCADE)
    access_key = models.CharField(_('Access key'), max_length=50, db_index=True)
    created = models.DateTimeField(verbose_name=_("Created date"), default=now, db_index=True)

    class Meta:
        verbose_name = _('Key to full recipe')
        verbose_name_plural = _('Keys to full recipe')

    def __str__(self):
        return f'Key to {self.recipe}'

    def expire_dt(self):
        expired = self.created + datetime.timedelta(days=settings.EXPIRATION_DATE_RECIPE_LINK)
        return now() >= expired


class VisitorData(AbstractIP):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'), blank=True,
                             null=True, on_delete=models.PROTECT)
    date = models.DateTimeField(verbose_name=_("Creation date"), default=now, db_index=True)

    class Meta:
        ordering = ['-date']
        verbose_name = _('Visitor Data Users')
        verbose_name_plural = _('Visitors Data Users')
        constraints = [
            models.UniqueConstraint(fields=['ip', 'user', 'user_agent'], name='unique_visitor')
        ]


def get_site_statistic():
    result = cache.get(f'SITE_STAT')
    if result is None:
        qs = Q(status=STATUS_PUBLISHED) | Q(status=STATUS_STICKY) | Q(status=STATUS_DRAFT) \
             | Q(status=STATUS_MODERATION) | Q(status=STATUS_LOCKED)
        recipes = Recipe.objects.filter(qs)
        users = get_user_model().objects.filter(is_active=True)
        devices = ConnectedDevice.objects.filter(enabled=True)
        devices_active = devices.filter(active=True)
        time_threshold = now() - timedelta(days=1)
        result = dict()
        result['recipes_today'] = recipes.filter(created_date__gt=time_threshold)
        result['recipes_all'] = recipes.count()
        result['recipes_pub'] = recipes.filter(status=STATUS_PUBLISHED).count()
        result['recipes_mod'] = recipes.filter(status=STATUS_MODERATION).count()
        result['recipes_draft'] = recipes.filter(status=STATUS_DRAFT).count()
        result['users_today'] = users.filter(last_login__gt=time_threshold)
        result['users_all'] = users.count()
        result['new_users_today'] = users.filter(date_joined__gt=time_threshold)
        result['users_banned'] = get_user_model().objects.filter(is_banned=True).count()
        result['users_punished'] = users.filter(status=PUNISHED).count()
        result['users_dubious'] = users.filter(status=DUBIOUS).count()
        result['users_user'] = users.filter(status=USER).count()
        result['users_pro'] = users.filter(status=PREMIUM).count()
        result['users_entity'] = users.filter(status=ENTITY).count()
        result['users_moderator'] = users.filter(status=MODERATOR).count()
        result['devices_all'] = devices.count()
        result['devices_active'] = devices_active.count()
        result['devices_bpl'] = devices_active.filter(type=DEVICE_BREWPILESS).count()
        result['devices_isp'] = devices_active.filter(type=DEVICE_ISPINDEL).count()
        cache.set(f'SITE_STAT', result)
    return result
