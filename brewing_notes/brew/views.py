import io
import json
import logging
import secrets

from datetime import timedelta, datetime
from itertools import chain

from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404, FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.generic import View, DetailView, TemplateView, ListView, CreateView, UpdateView, RedirectView
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from wkhtmltopdf.views import PDFTemplateView

from nnmware.core.constants import STATUS_STICKY, STATUS_PUBLISHED, STATUS_DELETE, STATUS_MODERATION, \
                                   STATUS_DRAFT, STATUS_LOCKED, STATUS_CHOICES, ACTION_DELETED, ACTION_UPDATED, \
                                   ACTION_CHOICES
from nnmware.core.exceptions import AccessError
from nnmware.core.imgutil import remove_thumbnails, remove_file
from nnmware.core.models import EmailValidation, Message, Action
from nnmware.core.signals import action
from nnmware.core.views import UserPathMixin
from nnmware.core.utils import make_key

from catalog.constants import TYPE_BEER, SPECIAL_BEER, TYPE_GRAIN, TYPE_FERMENTABLE, TYPE_ADDITIVE, TYPE_YEASTS, \
                              ACIDS, WATER_AGENT
from catalog.models import Malt, Fermentable, Hops, Yeasts, BeerStyle, WaterProfile, Misc, DEFAULT_GUIDES
from catalog.views import ListMixin, GetObjectMixin

from logdata.models import DeviceRawData

from publications.models import Topic

from .constants import (STATUS_USER, ADMIN, USE_BOIL, USE_PRIMARY, USE_MASH, SRM, USE_HOP_STAND,
                        STATUS_CONFORMITY, DEVICE_TYPE, LOG_BOTTLING, KILOGRAM, WATER_ADD_GYPSUM,
                        WATER_ADD_CALCIUM_CHLORIDE, WATER_ADD_EPSOM, WATER_ADD_MAGNESIUM_CHLORIDE,
                        WATER_ADD_CANNING_SALT, WATER_ADD_BAKING_SODA, WATER_ADD_CHALK, WATER_ADD_PICKLING_LIME,
                        WATER_ADD_LACTIC_ACID, WATER_ADD_CITRIC_ACID, WATER_ADD_ACETIC_ACID, WATER_ADD_PHOSPHORIC_ACID,
                        EQUIPMENT_TYPE, MODULE_OM_NONE, EQUIPMENT_FERMENTER, MODULE_OPERATION_MODE, USER,
                        PREMIUM)
from .exceptions import RequestLimitError, SendError
from .forms import AuthUserForm, RegisterUserForm, WaterIngredientFormSet, RecipeAddFullForm, MashFormSet, GrainFormSet, \
    FermentableFormSet, HopsFormSet, MiscFormSet, YeastsFormSet, WaterTargetFormSet, \
    LogFormSet, FermentationFormSet, UserForm, PrimerFormSet, RecipeForm, SendMessageForm, WaterOriginalFormSet
from .models import BrewUser, Recipe, FermentableIngredients, GrainIngredients, EmailConfirmation, HopsIngredients, \
    YeastsIngredients, ConnectedDevice, RecipeDataLog, get_site_statistic, UserTelegramProfile, WaterUserProfile, \
    MiscIngredients, AccessKeyFullRecipe, WaterOriginalProfile, WaterTargetProfile, WaterIngredient, Modules, \
    EquipmentModules
from .tgbot.dispatch import send_tg_admins, send_tg_user, send_tg_users
from .tgbot.dispatcher import process_telegram_event
from .tgbot.static_text import recipe_add, recipe_copy, recipe_on_moderation, new_user_register, user_deleted, \
    send_message_user, feedback_message, recipe_on_publication, user_banned, new_user_сonfirmation, \
    user_banned_trying_confirm, user_trial_activate, user_trial_refusal
from .utils import gravity_plato, dry_extract_recipe, srm_calc, \
                   ibu_calc, export_beerxml, attenuation, alco, plato_gravity, alco_old


logger = logging.getLogger(__name__)


def is_none(a):
    if a:
        return a
    else:
        return 0


class MainPageView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic_list'] = Topic.objects.filter(enabled=True).order_by('-position')
        return context


class Logout(LogoutView):
    next_page = 'main'


class BrewLoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = AuthUserForm

    def get_success_url(self):
        if self.request.GET.get('next', ''):
            redirect_to = self.request.GET.get('next', '')
        else:
            redirect_to = reverse('main')
        return redirect_to

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            if not user.is_confirm:
                messages.add_message(request, messages.ERROR, _('Account is not active. Follow the link in the email '
                                                                'to activate your account.'))
                return HttpResponseRedirect(reverse('main'))
            if user.is_active and not user.is_banned:
                if user.status == PREMIUM:
                    nw = datetime.today().date()
                    if user.premium_end is None:
                        premium_end = nw - timedelta(days=7)
                    else:
                        premium_end = user.premium_end
                    ends = premium_end - timedelta(days=7)
                    if premium_end < nw:
                        user.status = USER
                        user.limit_draft = 5
                        user.editor = False
                        user.tester = False
                        user.device_on_dashboard = None
                        if hasattr(user, 'usertelegramprofile'):
                            user.usertelegramprofile.enabled = False
                        if hasattr(user, 'pantry'):
                            user.pantry.enabled = False
                        for d in user.all_device:
                            d.enabled = False
                            d.save()
                        for m in user.all_bnc_modules:
                            m.enabled = False
                            m.save()
                        for e in user.all_equipment:
                            e.enabled = False
                            e.save()
                        user.save()
                        messages.add_message(request, messages.ERROR, _('The premium period has ended. '
                                                                        'You can renew it in the User Profile'))
                    elif nw >= ends:
                        messages.add_message(request, messages.WARNING, _(f'The premium period will end on '
                                                                          f'{user.premium_end.strftime("%d.%m.%Y")}. '
                                                                          f'You can renew it in the User Profile'))
                login(request, user)
                return HttpResponseRedirect(self.get_success_url())
            else:
                messages.add_message(request, messages.ERROR, _('User is not active or banned'))
        else:
            messages.add_message(request, messages.ERROR, _('Please enter the correct username and password. '
                                                            'Both fields can be case sensitive.'))
        return HttpResponseRedirect(reverse('main'))


class RegisterUserView(CreateView):
    model = BrewUser
    template_name = 'registration/register.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        if self.request.recaptcha_is_valid:
            form_valid = super().form_valid(form)
            form.save()
            msg = _('The user has been successfully created. '
                    'A letter has been sent to your email. '
                    'Follow the link in the email to activate your account.')
            messages.success(self.request, msg)
            send_tg_admins(new_user_register.format(login=form.cleaned_data.get('username'),
                                                    email=form.cleaned_data.get('email'),
                                                    ip=self.request.META.get('REMOTE_ADDR', '')))
            return form_valid
        else:
            return self.form_invalid(form)


class RestorePasswordView(TemplateView):
    template_name = 'registration/restore.html'

    def post(self, request, *args, **kwargs):
        if self.request.recaptcha_is_valid:
            try:
                username = request.POST.get('username')
                u = get_user_model().objects.get(username=username)
                if u.is_banned:
                    send_tg_admins(user_banned_trying_confirm.format(login=u.username,
                                                                     email=u.email,
                                                                     ip=request.META.get('REMOTE_ADDR', '')))
                    raise RequestLimitError
                results = EmailValidation.objects.filter(username=username).order_by('-created')
                if results:
                    time_threshold = now() - timedelta(minutes=10)
                    if results[0].created > time_threshold:
                        raise RequestLimitError
                results.delete()
                e = EmailValidation()
                e.username = u.username
                e.email = u.email
                e.password = get_user_model().objects.make_random_password()
                e.created = now()
                e.key = make_key(username)
                e.save()
                try:
                    curr_site = Site.objects.get_current()
                except Site.DoesNotExist:
                    return
                ctx = {
                    'key': e.key,
                    'user': e.username,
                    'site': curr_site.name,
                }
                email_subject = _('Password recovery for {}').format(curr_site.name)
                email_body = render_to_string('registration/recovery.txt', ctx)
                msg = EmailMessage(email_subject, email_body, to=[e.email])
                msg.send()
                messages.success(self.request, _('Link for recover password send at you email'))
            except ObjectDoesNotExist:
                messages.error(self.request, _('User not registered in system'))
            except RequestLimitError:
                messages.error(self.request, _('You have made too many requests. Please wait and try again later'))
            except Exception as err:
                messages.error(self.request, _(f'Unknown error'))
                logger.error(f'Recover password. Unknown error: {err}')
        return HttpResponseRedirect(reverse('main'))


class BrewUserRecoverView(RedirectView):
    """
    Recover password
    """
    def get(self, request, *args, **kwargs):
        key = self.kwargs['activation_key']
        try:
            time_threshold = now() - timedelta(days=1)
            results = EmailValidation.objects.filter(created__lt=time_threshold)
            results.delete()
            e = EmailValidation.objects.get(key=key)
            u = get_user_model().objects.get(username=e.username)
            u.set_password(e.password)
            u.save()
            user = authenticate(username=u.username, password=e.password)
            e.delete()
            login(self.request, u)
        except Exception:
            raise Http404
        return HttpResponseRedirect(reverse('user_detail', kwargs={'username': user.username}))


class ConfirmationEmailView(RedirectView):
    def get(self, request, *args, **kwargs):
        key = self.kwargs['confirm_key']
        user = EmailConfirmation.objects.confirmation(key.lower())
        if user:
            if user.is_confirm:
                login(self.request, user)
                send_tg_admins(new_user_сonfirmation.format(login=user.username,
                                                            email=user.email,
                                                            ip=request.META.get('REMOTE_ADDR', '')))
                return HttpResponseRedirect(reverse('user_detail', kwargs={'username': user.username}))
            else:
                messages.error(request, _('The activation period has expired'))
        else:
            messages.error(request, _('The activation period has expired'))
        return HttpResponseRedirect(reverse('main'))


class ConfirmationResendView(TemplateView):
    template_name = 'registration/confirmation_resend.html'

    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get('username')
            user = get_user_model().objects.get(username=username)
        except ObjectDoesNotExist:
            messages.error(request, _('The user does not exist'))
            return HttpResponseRedirect(reverse('main'))
        if user.is_banned:
            messages.success(request, _('The confirmation email has send'))
            send_tg_admins(user_banned_trying_confirm.format(login=user.username,
                                                             email=user.email,
                                                             ip=request.META.get('REMOTE_ADDR', '')))
        else:
            if user.is_confirm:
                messages.error(request, _('User is already confirmed'))
            else:
                try:
                    user.emailconfirmation.delete()
                    user.save()
                    messages.success(request, _('The confirmation email has send'))
                except Exception as err:
                    messages.error(request, _(f'Error send message'))
                    logger.error(f'Confirmation Resend Recover password. Error send message: {err}')
        return HttpResponseRedirect(reverse('main'))


class RecipesPublicListView(ListView):
    """
    Recipe public list all publishing and sticky
    """
    model = Recipe
    paginate_by = 20
    template_name = 'recipe/recipes_public_list.html'

    def get_queryset(self):
        qs = self.model.objects.active()
        style = self.request.GET.get('st', '')
        tp = self.request.GET.get('tp', '')
        order = '-public_date'
        if style and tp:
            new_qs = qs.filter(style=style, type=tp).order_by(order)
        elif style:
            new_qs = qs.filter(style=style).order_by(order)
        elif tp:
            new_qs = qs.filter(type=tp).order_by(order)
        else:
            new_qs = qs.order_by(order)
        return new_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = TYPE_BEER
        styles = self.model.objects.active().order_by('-style')
        context['all'] = styles
        filter_type = self.request.GET.get('tp', '')
        if filter_type:
            context['filter_type'] = TYPE_BEER[int(filter_type)][1]
        else:
            context['filter_type'] = ''
        filter_style = self.request.GET.get('st', '')
        if filter_style:
            context['filter_style'] = BeerStyle.objects.get(id=int(filter_style))
        else:
            context['filter_style'] = ''

        return context


class RecipePublicView(DetailView):
    """
    Public recipe view
    """
    model = Recipe
    context_object_name = 'recipe'
    template_name = 'recipe/recipe_public_detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, uid=self.kwargs['uid'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.object
        _srm = int(recipe.srm)
        if _srm > 40:
            _srm = 41
        context['srm_color'] = SRM[_srm]
        return context


class RecipesListView(LoginRequiredMixin, ListView):
    """
    Recipe list all publishing and sticky
    """
    model = Recipe
    login_url = '/login/'
    paginate_by = 40
    template_name = 'recipe/recipes_list.html'

    def get_queryset(self):
        qq = self.model.objects.active()
        grain = self.request.GET.get('grain', '')
        hop = self.request.GET.get('hop', '')
        yeast = self.request.GET.get('yeast', '')
        if grain:
            g = Malt.objects.get(pk=grain)
            qs = qq.filter(grainingredients__ingredient=g)
        elif hop:
            h = Hops.objects.get(pk=hop)
            qs = qq.filter(hopsingredients__ingredient=h)
        elif yeast:
            y = Yeasts.objects.get(pk=yeast)
            qs = qq.filter(yeastsingredients__ingredient=y)
        else:
            qs = qq
        style = self.request.GET.get('st', '')
        tp = self.request.GET.get('tp', '')
        order = self.request.GET.get('order_by', '-public_date')
        if order == 'rating':
            order = 'karma'
        elif order == '-rating':
            order = '-karma'
        if order == 'copies':
            order = 'views'
        elif order == '-copies':
            order = '-views'
        if style and tp:
            new_qs = qs.filter(style=style, type=tp).order_by(order)
        elif style:
            new_qs = qs.filter(style=style).order_by(order)
        elif tp:
            new_qs = qs.filter(type=tp).order_by(order)
        else:
            new_qs = qs.order_by(order)
        return new_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grain = self.request.GET.get('grain', '')
        hop = self.request.GET.get('hop', '')
        yeast = self.request.GET.get('yeast', '')
        if grain:
            context['grain'] = Malt.objects.get(pk=grain)
        if hop:
            context['hop'] = Hops.objects.get(pk=hop)
        if yeast:
            context['yeast'] = Yeasts.objects.get(pk=yeast)
        context['order_by'] = self.request.GET.get('order_by', 'name')
        context['type'] = TYPE_BEER
        return context


class RecipeView(LoginRequiredMixin, GetObjectMixin, DetailView):
    """
    Full recipe view
    """
    model = Recipe
    login_url = '/login/'
    context_object_name = 'recipe'
    template_name = 'recipe/recipe_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.object
        grain = recipe.grainingredients_set.all().order_by('-amount')
        grain_sum = grain.aggregate(Sum('amount'))['amount__sum']
        new = self.request.GET.get('new', '')
        value = self.request.GET.get('value', '')
        recalc = 1
        if new and value:
            if new == 'volume':
                recalc = float(value) / float(recipe.batch_size)
            elif new == 'weight':
                recalc = float(value) / float(grain_sum)
        misc = recipe.miscingredients_set.filter(use=USE_MASH)
        mash = sorted(chain(grain,
                            recipe.fermentableingredients_set.filter(use=USE_MASH),
                            misc.exclude(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))),
                            key=lambda instance: instance.use,
                            reverse=False)
        boil = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_BOIL),
                            recipe.hopsingredients_set.filter(use=USE_BOIL),
                            recipe.miscingredients_set.filter(use=USE_BOIL)),
                      key=lambda instance: instance.time,
                      reverse=True)
        chilling = list(chain(recipe.fermentableingredients_set.filter(use=USE_HOP_STAND),
                             recipe.hopsingredients_set.filter(use=USE_HOP_STAND),
                             recipe.miscingredients_set.filter(use=USE_HOP_STAND)))
        dry_hop = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_PRIMARY),
                             recipe.hopsingredients_set.filter(use=USE_PRIMARY),
                             recipe.miscingredients_set.filter(use=USE_PRIMARY)),
                         key=lambda instance: instance.time,
                         reverse=True)
        is_favorite = False
        if recipe.favorites.filter(id=self.request.user.id).exists():
            is_favorite = True
        _srm = int(recipe.srm)
        if _srm > 40:
            _srm = 41
        context['mash'] = mash
        context['boil'] = boil
        context['chilling'] = chilling
        context['dry_hop'] = dry_hop
        context['is_favorite'] = is_favorite
        context['grain_sum'] = grain_sum
        context['water_sum'] = recipe.mash_water + recipe.sparge_water
        context['hop_sum'] = recipe.hopsingredients_set.all().aggregate(Sum('amount'))['amount__sum']
        context['srm_color'] = SRM[_srm]
        context['recalc'] = recalc
        context['att'] = attenuation(recipe.OG, recipe.FG)
        return context


class RecipePublishingView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, RedirectView):
    """
    Publishing recipe
    """
    model = Recipe
    login_url = '/login/'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user:
            return True
        else:
            return False

    def get_success_url(self):
        return reverse_lazy('user_recipes', args=[self.request.user.username])

    def post(self, request, *args, **kwargs):
        consent = request.POST.get('consent', None)
        if consent:
            try:
                self.object = self.get_object()
                self.object.private = False
                self.object.status = STATUS_MODERATION
                self.object.save()
                send_tg_admins(recipe_on_moderation.format(user=self.object.user.username,
                                                           name=self.object.name))
                messages.success(request, _('The recipe has been successfully submitted for moderation'))
            except Exception as err:
                logger.error(f'Error publishing recipe: {err}')
                messages.error(request, _('Error publishing'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return HttpResponseRedirect(self.object.get_absolute_url())


class RecipeIngredientsListView(LoginRequiredMixin, GetObjectMixin, DetailView):
    """
    Printable recipe ingredients list
    """
    model = Recipe
    login_url = '/login/'
    context_object_name = 'recipe'
    template_name = 'recipe/recipe_list_ingredients.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.object
        context['ingredients'] = recipe.get_list_ingredients
        return context


class RecipeShareLiteView(DetailView):
    """
    Printable recipe with short link
    """
    model = Recipe
    context_object_name = 'recipe'
    template_name = 'recipe/recipe_share_lite.html'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, uid=self.kwargs['uid'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == STATUS_DELETE:
            raise Http404
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mash = list(chain(self.object.grainingredients_set.all(),
                          self.object.fermentableingredients_set.filter(use=USE_MASH),
                          self.object.miscingredients_set.filter(use=USE_MASH)))
        boil = sorted(chain(self.object.fermentableingredients_set.filter(use=USE_BOIL),
                          self.object.hopsingredients_set.filter(use=USE_BOIL),
                          self.object.miscingredients_set.filter(use=USE_BOIL)),
                      key=lambda instance: instance.time,
                      reverse=True)
        chilling = self.object.hopsingredients_set.filter(use=1).order_by('temp')
        dry_hop = sorted(chain(self.object.fermentableingredients_set.filter(use=USE_PRIMARY),
                             self.object.hopsingredients_set.filter(use=USE_PRIMARY),
                             self.object.miscingredients_set.filter(use=USE_PRIMARY)),
                       key=lambda instance: instance.time,
                       reverse=True)
        _srm = int(self.object.srm)
        if _srm > 40:
            _srm = 41
        context['srm_color'] = SRM[_srm]
        context['mash'] = mash
        context['boil'] = boil
        context['chilling'] = chilling
        context['dry_hop'] = dry_hop
        return context


class RecipeShareFullView(DetailView):
    """
    Full recipe view
    """
    model = Recipe
    login_url = '/login/'
    context_object_name = 'recipe'
    template_name = 'recipe/recipe_share_full.html'

    def get_object(self):
        ak = get_object_or_404(AccessKeyFullRecipe, access_key=self.kwargs['key'])
        return ak.recipe

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.get_temp_full_link() is None or self.object.status == STATUS_DELETE:
            raise Http404
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        grain = recipe.grainingredients_set.all().order_by('-amount')
        grain_sum = grain.aggregate(Sum('amount'))['amount__sum']
        misc = recipe.miscingredients_set.filter(use=USE_MASH)
        water = recipe.miscingredients_set.filter(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))
        mash = sorted(chain(grain,
                          recipe.fermentableingredients_set.filter(use=USE_MASH),
                          misc.exclude(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))),
                      key=lambda instance: instance.use,
                      reverse=False)
        boil = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_BOIL),
                            recipe.hopsingredients_set.filter(use=USE_BOIL),
                            recipe.miscingredients_set.filter(use=USE_BOIL)),
                      key=lambda instance: instance.time,
                      reverse=True)
        chilling = list(chain(recipe.fermentableingredients_set.filter(use=USE_HOP_STAND),
                             recipe.hopsingredients_set.filter(use=USE_HOP_STAND),
                             recipe.miscingredients_set.filter(use=USE_HOP_STAND)))
        dry_hop = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_PRIMARY),
                             recipe.hopsingredients_set.filter(use=USE_PRIMARY),
                             recipe.miscingredients_set.filter(use=USE_PRIMARY)),
                         key=lambda instance: instance.time,
                         reverse=True)
        is_favorite = False
        if recipe.favorites.filter(id=self.request.user.id).exists():
            is_favorite = True
        _srm = int(recipe.srm)
        if _srm > 40:
            _srm = 41
        context['mash'] = mash
        context['water_salts'] = water
        context['boil'] = boil
        context['chilling'] = chilling
        context['dry_hop'] = dry_hop
        context['is_favorite'] = is_favorite
        context['grain_sum'] = grain_sum
        context['water_sum'] = recipe.mash_water + recipe.sparge_water
        context['hop_sum'] = recipe.hopsingredients_set.all().aggregate(Sum('amount'))['amount__sum']
        context['srm_color'] = SRM[_srm]
        context['att'] = attenuation(recipe.OG, recipe.FG)
        return context


class RecipeAddFullView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Add full recipe
    """
    model = Recipe
    login_url = '/login/'
    form_class = RecipeAddFullForm
    template_name = 'recipe/recipe_add.html'

    def get_success_url(self):
        return reverse_lazy('recipe_detail', args=[self.object.slug])

    def test_func(self):
        if self.request.user.ability_to_add:
            return True
        else:
            messages.error(self.request, _('Drafts limit is over'))
            return False

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        mash_form = MashFormSet(prefix='mash')
        grain_form = GrainFormSet(prefix='grain')
        ferm_form = FermentableFormSet(prefix='ferm')
        hops_form = HopsFormSet(prefix='hops')
        misc_form = MiscFormSet(prefix='misc')
        yeast_form = YeastsFormSet(prefix='yeast')
        water_original_form = WaterOriginalFormSet(prefix='water_target')
        water_target_form = WaterTargetFormSet(prefix='water_original')
        water_ing_form = WaterIngredientFormSet(prefix='water_ing')
        log_form = LogFormSet(prefix='log')
        fermentation_form = FermentationFormSet(prefix='fermentation')
        priming_form = PrimerFormSet(prefix='prim')
        return self.render_to_response(self.get_context_data(form=form,
                                                             mash_form=mash_form,
                                                             grain_form=grain_form,
                                                             ferm_form=ferm_form,
                                                             hops_form=hops_form,
                                                             misc_form=misc_form,
                                                             yeast_form=yeast_form,
                                                             water_original_form=water_original_form,
                                                             water_target_form=water_target_form,
                                                             water_ing_form=water_ing_form,
                                                             log_form=log_form,
                                                             fermentation_form=fermentation_form,
                                                             priming_form=priming_form))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formsets with the passed POST variables and then checking them for
        validity.
        """
        self.object = None
        form = self.form_class(self.request.POST, self.request.FILES)
        mash_form = MashFormSet(self.request.POST, prefix='mash')
        grain_form = GrainFormSet(self.request.POST, prefix='grain')
        ferm_form = FermentableFormSet(self.request.POST, prefix='ferm')
        hops_form = HopsFormSet(self.request.POST, prefix='hops')
        misc_form = MiscFormSet(self.request.POST, prefix='misc')
        yeast_form = YeastsFormSet(self.request.POST, prefix='yeast')
        water_original_form = WaterOriginalFormSet(self.request.POST, prefix='water_original')
        water_target_form = WaterTargetFormSet(self.request.POST, prefix='water_target')
        water_ing_form = WaterIngredientFormSet(self.request.POST, prefix='water_ing')
        log_form = LogFormSet(self.request.POST, prefix='log')
        fermentation_form = FermentationFormSet(self.request.POST, prefix='fermentation')
        priming_form = PrimerFormSet(self.request.POST, prefix='prim')

        if (form.is_valid() and mash_form.is_valid() and grain_form.is_valid() and
            ferm_form.is_valid() and hops_form.is_valid() and misc_form.is_valid() and
            yeast_form.is_valid() and water_original_form.is_valid() and water_target_form.is_valid() and
            water_ing_form.is_valid() and log_form.is_valid() and
            fermentation_form.is_valid() and priming_form.is_valid()):
            return self.form_valid(form, mash_form, grain_form, ferm_form, hops_form,
                                   misc_form, yeast_form, water_target_form, water_original_form,  water_ing_form,
                                   log_form, fermentation_form, priming_form)
        else:
            return self.form_invalid(form, mash_form, grain_form, ferm_form, hops_form,
                                     misc_form, yeast_form, log_form,
                                     water_target_form, water_original_form, water_ing_form,
                                     fermentation_form, priming_form)

    def form_valid(self, form, mash_form, grain_form, ferm_form, hops_form, misc_form,
                   yeast_form, water_target_form, water_original_form,  water_ing_form,
                   log_form, fermentation_form, priming_form):
        """
        Called if all forms are valid. Creates a Recipe instance along with
        associated Ingredients and Instructions and then redirects to a
        success page.
        """
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.enabled = True
        self.object.save()
        mash_form.instance = self.object
        mash_form.save()
        grain_form.instance = self.object
        grain_form.save()
        ferm_form.instance = self.object
        ferm_form.save()
        hops_form.instance = self.object
        hops_form.save()
        misc_form.instance = self.object
        misc_form.save()
        yeast_form.instance = self.object
        yeast_form.save()
        water_original_form.instance = self.object
        water_original_form.save()
        water_target_form.instance = self.object
        water_target_form.save()
        water_ing_form.instance = self.object
        water_ing_form.save()
        log_form.instance = self.object
        log_form.save()
        fermentation_form.instance = self.object
        fermentation_form.save()
        priming_form.instance = self.object
        priming_form.save()
        send_tg_admins(recipe_add.format(user=self.object.user.username,
                                         name=self.object.name,
                                         style=self.object.style))
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, mash_form, grain_form, ferm_form, hops_form, misc_form,
                     yeast_form, water_original_form, water_target_form, water_ing_form, log_form, fermentation_form, priming_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(self.get_context_data(form=form,
                                                             mash_form=mash_form,
                                                             grain_form=grain_form,
                                                             ferm_form=ferm_form,
                                                             hops_form=hops_form,
                                                             misc_form=misc_form,
                                                             yeast_form=yeast_form,
                                                             water_original_form=water_original_form,
                                                             water_target_form=water_target_form,
                                                             water_ing_form=water_ing_form,
                                                             log_form=log_form,
                                                             fermentation_form=fermentation_form,
                                                             priming_form=priming_form))


class RecipeEditFullView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, UpdateView):
    """
    Edit lite recipe
    """
    model = Recipe
    login_url = '/login/'
    form_class = RecipeAddFullForm
    template_name = 'recipe/recipe_add.html'

    def get_success_url(self):
        return reverse_lazy('recipe_detail', args=[self.object.slug])

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user and self.object.status == STATUS_DRAFT:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        mash_form = MashFormSet(instance=self.object, prefix='mash')
        grain_form = GrainFormSet(instance=self.object, prefix='grain')
        ferm_form = FermentableFormSet(instance=self.object, prefix='ferm')
        hops_form = HopsFormSet(instance=self.object, prefix='hops')
        misc_form = MiscFormSet(instance=self.object, prefix='misc')
        yeast_form = YeastsFormSet(instance=self.object, prefix='yeast')
        water_original_form = WaterOriginalFormSet(instance=self.object, prefix='water_target')
        water_target_form = WaterTargetFormSet(instance=self.object, prefix='water_original')
        water_ing_form = WaterIngredientFormSet(instance=self.object, prefix='water_ing')
        log_form = LogFormSet(instance=self.object, prefix='log')
        fermentation_form = FermentationFormSet(instance=self.object, prefix='fermentation')
        priming_form = PrimerFormSet(instance=self.object, prefix='prim')
        return self.render_to_response(
            self.get_context_data(form=form,
                                  mash_form=mash_form,
                                  grain_form=grain_form,
                                  ferm_form=ferm_form,
                                  hops_form=hops_form,
                                  misc_form=misc_form,
                                  yeast_form=yeast_form,
                                  water_original_form=water_original_form,
                                  water_target_form=water_target_form,
                                  water_ing_form=water_ing_form,
                                  log_form=log_form,
                                  fermentation_form=fermentation_form,
                                  priming_form=priming_form))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formsets with the passed POST variables and then checking them for
        validity.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        mash_form = MashFormSet(self.request.POST, instance=self.object, prefix='mash')
        grain_form = GrainFormSet(self.request.POST, instance=self.object, prefix='grain')
        ferm_form = FermentableFormSet(self.request.POST, instance=self.object, prefix='ferm')
        hops_form = HopsFormSet(self.request.POST, instance=self.object, prefix='hops')
        misc_form = MiscFormSet(self.request.POST, instance=self.object, prefix='misc')
        yeast_form = YeastsFormSet(self.request.POST, instance=self.object, prefix='yeast')
        water_original_form = WaterOriginalFormSet(self.request.POST, instance=self.object, prefix='water_target')
        water_target_form = WaterTargetFormSet(self.request.POST, instance=self.object, prefix='water_original')
        water_ing_form = WaterIngredientFormSet(self.request.POST, instance=self.object, prefix='water_ing')
        log_form = LogFormSet(self.request.POST, instance=self.object, prefix='log')
        fermentation_form = FermentationFormSet(self.request.POST, instance=self.object, prefix='fermentation')
        priming_form = PrimerFormSet(self.request.POST, instance=self.object, prefix='prim')

        if (form.is_valid() and mash_form.is_valid() and grain_form.is_valid() and
            ferm_form.is_valid() and hops_form.is_valid() and misc_form.is_valid() and
            yeast_form.is_valid() and water_original_form.is_valid() and water_target_form.is_valid() and
            water_ing_form.is_valid() and log_form.is_valid() and
            fermentation_form.is_valid() and priming_form.is_valid()):
            return self.form_valid(form, mash_form, grain_form, ferm_form, hops_form,
                                   misc_form, yeast_form, water_original_form, water_target_form,
                                   water_ing_form, log_form, fermentation_form, priming_form)
        else:
            return self.form_invalid(form, mash_form, grain_form, ferm_form, hops_form,
                                     misc_form, yeast_form, water_original_form, water_target_form,
                                     water_ing_form, log_form, fermentation_form, priming_form)

    def form_valid(self, form, mash_form, grain_form, ferm_form, hops_form, misc_form,
                   yeast_form, water_original_form, water_target_form, water_ing_form,
                   log_form, fermentation_form, priming_form):
        """
        Called if all forms are valid. Creates a Recipe instance along with
        associated Ingredients and Instructions and then redirects to a
        success page.
        """
        try:
            self.object = form.save(commit=False)
            self.object.user = self.request.user
            self.object.enabled = True
            self.object.save()
            mash_form.instance = self.object
            mash_form.save()
            grain_form.instance = self.object
            grain_form.save()
            ferm_form.instance = self.object
            ferm_form.save()
            hops_form.instance = self.object
            hops_form.save()
            misc_form.instance = self.object
            misc_form.save()
            yeast_form.instance = self.object
            yeast_form.save()
            water_original_form.instance = self.object
            water_original_form.save()
            water_target_form.instance = self.object
            water_target_form.save()
            water_ing_form.instance = self.object
            water_ing_form.save()
            log_form.instance = self.object
            log_form.save()
            fermentation_form.instance = self.object
            fermentation_form.save()
            priming_form.instance = self.object
            priming_form.save()
        except Exception as err:
            raise ValueError(err)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, mash_form, grain_form, ferm_form, hops_form, misc_form,
                     yeast_form, water_original_form, water_target_form, water_ing_form,
                     log_form, fermentation_form, priming_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(self.get_context_data(form=form,
                                                             mash_form=mash_form,
                                                             grain_form=grain_form,
                                                             ferm_form=ferm_form,
                                                             hops_form=hops_form,
                                                             misc_form=misc_form,
                                                             yeast_form=yeast_form,
                                                             water_original_form=water_original_form,
                                                             water_target_form=water_target_form,
                                                             water_ing_form=water_ing_form,
                                                             log_form=log_form,
                                                             fermentation_form=fermentation_form,
                                                             priming_form=priming_form))


class RecipeCopyView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, RedirectView):
    """
    Сopying a recipe to your drafts
    """
    model = Recipe
    login_url = '/login/'

    def test_func(self):
        if self.request.user.ability_to_add:
            return True
        else:
            messages.error(self.request, _('Drafts limit is over'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            recipe = self.get_object()
            new_batch_size = request.POST.get('new_batch_size', '')
            recalc = 1
            if new_batch_size:
                recalc = float(new_batch_size) / float(recipe.batch_size)
            copy_recipe = recipe.create_copy(request.user, abs(recalc))
            messages.success(request, _(f'Recipe copied successfully'))
            send_tg_admins(recipe_copy.format(user=recipe.user.username,
                                              name=recipe.name))
            return HttpResponseRedirect(reverse_lazy('recipe_edit', args=[copy_recipe.slug]))
        except Exception as err:
            logger.error(f'Recipe copy error: {err}')
            messages.error(request, _(f'Recipe copy error'))
            return HttpResponseRedirect(recipe.get_absolute_url())


class RecipePDFView(LoginRequiredMixin, GetObjectMixin, PDFTemplateView):
    """
    Export a recipe to pdf file
    """
    model = Recipe
    login_url = '/login/'
    template_name = 'recipe/recipe_detail_pdf.html'
    cmd_options = {
        'margin-top': 3,
        'margin-bottom': 5,
    }

    def get_filename(self):
        self.object = self.get_object()
        return f'{self.object.name}.pdf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        grain = recipe.grainingredients_set.all()
        rc = self.request.GET.get('recalc', '')
        if rc:
            recalc = float(rc.replace(',', '.'))
        else:
            recalc = 1
        mash = list(chain(grain,
                          recipe.fermentableingredients_set.filter(use=USE_MASH),
                          recipe.miscingredients_set.filter(use=USE_MASH)))
        boil = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_BOIL),
                          recipe.hopsingredients_set.filter(use=USE_BOIL),
                          recipe.miscingredients_set.filter(use=USE_BOIL)),
                      key=lambda instance: instance.time,
                      reverse=True)
        chilling = recipe.hopsingredients_set.filter(use=1).order_by('temp')
        dry_hop = list(chain(recipe.fermentableingredients_set.filter(use=USE_PRIMARY),
                             recipe.hopsingredients_set.filter(use=USE_PRIMARY),
                             recipe.miscingredients_set.filter(use=USE_PRIMARY)))
        context['recipe'] = recipe
        context['mash'] = mash
        context['boil'] = boil
        context['chilling'] = chilling
        context['dry_hop'] = dry_hop
        context['grain_sum'] = grain.aggregate(Sum('amount'))['amount__sum']
        context['recalc'] = recalc
        return context


class RecipeBrewCardPDFView(LoginRequiredMixin, GetObjectMixin, PDFTemplateView):
    """
    Export a recipe to pdf file
    """
    model = Recipe
    login_url = '/login/'
    template_name = 'recipe/recipe_brewcard_pdf.html'
    cmd_options = {
        'margin-top': 5,
        'margin-bottom': 5,
        'margin-right': 7,
    }

    def get_filename(self):
        self.object = self.get_object()
        return f'{self.object.name}.pdf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        grain = recipe.grainingredients_set.all()
        rc = self.request.GET.get('recalc', '')
        if rc:
            recalc = float(rc.replace(',', '.'))
        else:
            recalc = 1
        mash = list(chain(grain,
                          recipe.fermentableingredients_set.filter(use=USE_MASH),
                          recipe.miscingredients_set.filter(use=USE_MASH)))
        boil = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_BOIL),
                          recipe.hopsingredients_set.filter(use=USE_BOIL),
                          recipe.miscingredients_set.filter(use=USE_BOIL)),
                      key=lambda instance: instance.time,
                      reverse=True)
        chilling = recipe.hopsingredients_set.filter(use=1).order_by('temp')
        dry_hop = list(chain(recipe.fermentableingredients_set.filter(use=USE_PRIMARY),
                             recipe.hopsingredients_set.filter(use=USE_PRIMARY),
                             recipe.miscingredients_set.filter(use=USE_PRIMARY)))
        context['recipe'] = recipe
        context['mash'] = mash
        context['boil'] = boil
        context['chilling'] = chilling
        context['dry_hop'] = dry_hop
        context['grain_sum'] = grain.aggregate(Sum('amount'))['amount__sum']
        context['water_sum'] = recipe.mash_water + recipe.sparge_water
        context['hop_sum'] = recipe.hopsingredients_set.all().aggregate(Sum('amount'))['amount__sum']
        context['recalc'] = recalc
        return context


class RecipeLabelPDFView(LoginRequiredMixin, GetObjectMixin, PDFTemplateView):
    """
    Export a recipe to pdf file
    """
    model = Recipe
    # context_object_name = 'recipe'
    login_url = '/login/'
    template_name = 'recipe/recipe_label_pdf.html'
    cmd_options = {
        'margin-top': 3,
        'margin-bottom': 5,
    }

    def get_filename(self):
        self.object = self.get_object()
        return f'{self.object.name}.pdf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        data_bottling = recipe.brewinglog_set.filter(event=LOG_BOTTLING)
        if data_bottling:
            bottling = data_bottling[0].date
        else:
            bottling = None
        context['recipe'] = recipe
        context['bottling'] = bottling
        context['rows_label'] = range(3)
        return context


class RecipeBXMLView(LoginRequiredMixin, GetObjectMixin, View):
    """
    Export a recipe to BeerXML file
    """
    model = Recipe
    login_url = '/login/'

    def get_filename(self):
        self.object = self.get_object()
        return f'{self.object.name}.xml'

    def get(self, request, *args, **kwargs):
        recipe = self.get_object()
        xml = export_beerxml(recipe)
        buffer = io.BytesIO()
        buffer.write(xml)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=self.get_filename())


class RecipeDeleteView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, DetailView):
    """
    Delete recipe
    """
    model = Recipe
    login_url = '/login/'
    template_name = 'user/user_recipes.html'

    def get_success_url(self):
        return reverse_lazy('user_recipes', args=[self.request.user.username])

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.enabled = False
            self.object.status = STATUS_DELETE
            pics = self.object.allpics
            self.object.pics = len(pics)
            if pics:
                for pic in pics:
                    remove_thumbnails(pic.img.path)
                    remove_file(pic.img.path)
                    pic.delete()
            self.object.save()
            messages.success(request, _(f'Recipe {self.object.name} successfully deleted'))
            action.send(self.request.user, verb=_(f'Recipe {self.object.name} deleted'),
                        action_type=ACTION_DELETED,
                        description=_(f'User: {self.object.user.username} deleted recipe: {self.object.name}'),
                        target=self.object,
                        request=self.request)
        except Exception as err:
            logger.error(f'Recipe delete error: {err}')
            messages.error(request, _('Recipe delete error'))
        return HttpResponseRedirect(self.get_success_url())


class RecipeAnalysisView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, DetailView):
    """
    Calculate recipe
    """
    model = Recipe
    login_url = '/login/'
    context_object_name = 'recipe'
    template_name = 'recipe/recipe_analisis.html'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user.is_pro:
            return True
        else:
            return False

    def get_success_url(self):
        return reverse_lazy('recipe_detail', args=[self.object.slug])

    def get(self, request, *args, **kwargs):
        recipe = self.get_object()
        error = False
        if recipe.PBG == 1.000:
            messages.error(request, _(f'To calculate the parameters, the "Pre boil size" must not be zero'))
            error = True
        if recipe.pre_boil_size == 0:
            messages.error(request, _(f'To calculate the parameters, the "Pre boil gravity" must not be 1.000'))
            error = True
        if error:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        recipe = self.get_object()
        alco = self.request.POST.get('alco_check', False)
        ibu = self.request.POST.get('ibu_check', False)
        srm = self.request.POST.get('srm_check', False)
        eff = self.request.POST.get('eff_check', False)
        try:
            if alco == 'on':
                recipe.abv = alco_old(recipe.OG, recipe.FG)
            if ibu == 'on':
                recipe.ibu = int(self.request.POST.get('ibu', 0))
            if srm == 'on':
                recipe.srm = float(self.request.POST.get('srm', 0))
            if eff == 'on':
                recipe.efficiency_mash = float(self.request.POST.get('eff', 0))
            if alco == 'on' or ibu == 'on' or srm == 'on' or eff == 'on':
                recipe.save()
                messages.success(self.request, _('Recipe parameters have been successfully updated'))
        except Exception as err:
            logger.error(f'Error updating recipe parameters: {err}')
            messages.error(request, _(f'Error updating recipe parameters'))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rcp = self.object
        grain = rcp.grainingredients_set.all()
        ferms = rcp.fermentableingredients_set.all()
        context['alco'] = alco(rcp.OG, rcp.FG)
        total_grain = float(grain.aggregate(Sum('amount'))['amount__sum'])
        context['total_grain'] = total_grain
        context['total_water'] = float(rcp.mash_water + rcp.sparge_water)
        dry_extract = dry_extract_recipe(grain)
        context['hm'] = round(float(rcp.mash_water) / total_grain, 1)
        context['color'] = srm_calc(grain, ferms, rcp.batch_size)
        context['ibu'] = ibu_calc(rcp, total_grain)
        context['dry_extract'] = dry_extract
        context['att'] = attenuation(rcp.OG, rcp.FG)
        yeast = rcp.yeastsingredients_set.all()[0]
        pbg = gravity_plato(rcp.PBG) * (1 - float(yeast.ingredient.attenuation) / 100)
        context['pbg'] = plato_gravity(pbg)
        if rcp.pre_boil_size:
            context['evaporation'] = round((1 - rcp.batch_size / rcp.pre_boil_size) * 100, 1)
            context['absorption'] = round(float(rcp.mash_water + rcp.sparge_water - rcp.pre_boil_size) / total_grain, 2)
            if rcp.PBG:
                context['efficiency'] = round(float(rcp.pre_boil_size) * (gravity_plato(rcp.PBG)) / dry_extract, 1)
            else:
                context['efficiency'] = 0
        else:
            context['evaporation'] = 0
            context['absorption'] = 0
        return context


class RecipeChartSaveView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Add chart data in Recipe
    """
    model = Recipe
    login_url = '/login/'
    success_url = reverse_lazy('main')

    def test_func(self):
        if self.request.user.is_pro:
            return True
        else:
            messages.error(self.request, _('Only Premium user'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            device = get_object_or_404(ConnectedDevice, pk=kwargs['object_id'])
            if device.user == request.user:
                recipe = request.POST.get('recipe', None)
                recipe = get_object_or_404(Recipe, pk=recipe)
            else:
                raise AccessError
            from_time = request.POST.get('from_time', None)
            from_date = request.POST.get('from_date', None)
            to_time = request.POST.get('to_time', None)
            to_date = request.POST.get('to_date', None)
            from_ = f'{from_date} {from_time}'
            to_ = f'{to_date} {to_time}'
            from_d = datetime.strptime(from_, '%Y-%m-%d %H:%M')
            to_d = datetime.strptime(to_, '%Y-%m-%d %H:%M')
            logs = device.devicedatalog_set.filter(created_date__gte=from_d,
                                                   created_date__lte=to_d)
            temp = request.POST.get('temp', 'beer')
            data = list()
            for i in logs:
                item = {
                    'date': i.created_date,
                    'grav': float(i.gravity)
                }
                if temp == 'beer':
                    item['temp'] = float(i.beer_temp)
                elif temp == 'fridge':
                    item['temp'] = float(i.fridge_temp)
                else:
                    item['temp'] = float(i.aux_temp)
                data.append(item)
            RecipeDataLog.objects.update_or_create(recipe=recipe,
                                                   defaults={'device': device.type,
                                                   'data': json.dumps(data, cls=DjangoJSONEncoder)},)
            messages.success(request, _(f'Data added to recipe'))
            return HttpResponseRedirect(recipe.get_absolute_url())
        except Exception as err:
            logger.error(f'Error save chart data: {err}')
            messages.error(request, _(f'Error save chart data'))
            return HttpResponseRedirect(reverse_lazy(request.META.get('HTTP_REFERER')))


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, UserPathMixin, DetailView):
    """
    User settings
    """
    model = BrewUser
    form_class = UserForm
    login_url = '/login/'
    template_name = 'user/user_detail.html'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_device'] = DEVICE_TYPE
        return context


class UserRecipesListView(LoginRequiredMixin, UserPathMixin, ListView):
    """
    List recipes user
    """
    model = BrewUser
    login_url = '/login/'
    paginate_by = 20
    template_name = 'user/user_recipes.html'

    def get_queryset(self):
        self.object = self.get_object()
        rcp = Recipe.objects.filter(user=self.object, enabled=True)
        if self.request.user == self.object:
            recipes = rcp.filter(Q(status=STATUS_PUBLISHED) | Q(status=STATUS_STICKY) |
                                 Q(status=STATUS_DRAFT) | Q(status=STATUS_MODERATION))
        else:
            recipes = rcp.filter(Q(status=STATUS_PUBLISHED) | Q(status=STATUS_STICKY))
        order = self.request.GET.get('order_by', '-created_date')
        result_list = recipes.order_by(order)
        return result_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.object
        return context


class UserFavoritesListView(LoginRequiredMixin, UserPassesTestMixin, UserPathMixin, ListView):
    """
    List recipes user
    """
    model = BrewUser
    login_url = '/login/'
    paginate_by = 20
    template_name = 'user/user_favorites.html'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object:
            return True
        else:
            return False

    def get_queryset(self):
        self.object = self.get_object()
        recipes = Recipe.objects.filter(favorites__pk=self.object.pk)
        order = self.request.GET.get('order_by', '-created_date')
        result_list = recipes.order_by(order)
        return result_list


class UserMessagesInboxView(LoginRequiredMixin, UserPathMixin, ListView):
    """
    List inbox messages user
    """
    model = Message
    login_url = '/login/'
    paginate_by = 20
    template_name = 'user/user_messages_inbox.html'

    def get_queryset(self):
        qs = self.model.objects.inbox_for(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = self.model.objects.inbox_for(self.request.user).count()
        return context


class UserMessagesSendboxView(LoginRequiredMixin, UserPathMixin, ListView):
    """
    List sendbox messages user
    """
    model = Message
    login_url = '/login/'
    paginate_by = 20
    template_name = 'user/user_messages_sendbox.html'

    def get_queryset(self):
        qs = self.model.objects.outbox_for(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = self.model.objects.outbox_for(self.request.user).count()
        return context


class UserMessagesNewView(LoginRequiredMixin, UserPathMixin, CreateView):
    """
    Send message
    """
    model = Message
    login_url = '/login/'
    form_class = SendMessageForm
    template_name = 'user/user_messages_new.html'
    success_url = reverse_lazy('user_messages_sendbox')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = BrewUser.objects.filter(is_confirm=True, is_active=True).exclude(id=self.request.user.id)
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid:
            try:
                sender = request.user
                recipient = get_user_model().objects.get(pk=request.POST.get('recipient'))
                subject = request.POST.get('subject')
                if not subject:
                    subject = _('no subject')
                body = request.POST.get('body', None)
                if sender == recipient:
                    raise SendError
                if body is None:
                    raise SendError
                msg = Message()
                msg.subject = subject
                msg.ip = request.META['REMOTE_ADDR']
                msg.user_agent = request.META['HTTP_USER_AGENT']
                msg.body = body
                msg.sender = sender
                msg.recipient = recipient
                msg.sent_at = now()
                msg.save()
                messages.success(request, _(f'Message {recipient} sent successfully'))
                send_tg_user(recipient,
                             send_message_user.format(user=request.user,
                                                      time=msg.sent_at.strftime("%d.%m.%Y %H:%M"),
                                                      subject=subject,
                                                      message=body[:100]))
            except SendError:
                messages.error(request, _(f'Unable to send message'))
            except Exception as err:
                logger.error(f'Error sending message: {err}')
                messages.error(request, _(f'Error sending message'))
            return HttpResponseRedirect(self.success_url)
        else:
            return HttpResponseRedirect(request.path)


class UserDeviceAddView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Add device
    """
    model = ConnectedDevice
    login_url = '/login/'

    def test_func(self):
        if self.request.user.device_available:
            return True
        else:
            messages.error(self.request, _('Device limit is over'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            device = self.model()
            device.user = request.user
            device.name = request.POST.get('name', 'device')
            device.type = request.POST.get('type', 99)
            device.save()
            return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Add device error: {err}')
            messages.error(request, _(f'Add device error'))
            return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))


class UserModuleAddView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Add user module
    """
    model = Modules
    login_url = '/login/'

    def test_func(self):
        if self.request.user.module_available:
            return True
        else:
            messages.error(self.request, _('Modules limit is over'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            module = self.model()
            module.user = request.user
            module.name = request.POST.get('name', 'module')
            module.active = True
            module.save()
            return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Add module error: {err}')
            messages.error(request, _(f'Add module error'))
            return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))


class UserDeviceSettingView(LoginRequiredMixin, RedirectView):
    """
    Save device settings
    """
    model = BrewUser
    login_url = '/login/'

    def post(self, request, *args, **kwargs):
        try:
            dev_id = request.POST.get('select_main_device', False)
            usr = request.user
            if dev_id:
                dev = get_object_or_404(ConnectedDevice, pk=int(dev_id), enabled=True)
                if dev.user != usr:
                    raise AccessError
                usr.device_on_dashboard = dev
            else:
                usr.device_on_dashboard = None
            usr.save()
            messages.success(request, _(f'Settings saved successfully'))
        except AccessError:
            messages.error(request, _(f'You cannot add device on dashboard'))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Add device on dashboard error: {err}')
            messages.error(request, _(f'Add device on dashboard error'))
        return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))


class UserWaterAddView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Add user water profile
    """
    model = WaterUserProfile
    login_url = '/login/'

    def test_func(self):
        if self.request.user.ability_to_add_water:
            return True
        else:
            messages.error(self.request, _('User water profile limit is over'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            water_id = request.POST.get('water_id', '')
            if water_id:
                water = get_object_or_404(WaterUserProfile, pk=int(water_id))
            else:
                water = self.model()
                water.user = request.user
            water.name = request.POST.get('water_name', secrets.token_hex()[:8])
            water.description = request.POST.get('water_desc', '')
            water.calcum = int(request.POST.get('water_ca', 0))
            water.bicarbonate = int(request.POST.get('water_hco', 0))
            water.sulfate = int(request.POST.get('water_so', 0))
            water.chloride = int(request.POST.get('water_cl', 0))
            water.sodium = int(request.POST.get('water_na', 0))
            water.magnesium = int(request.POST.get('water_mg', 0))
            water.ph = float(request.POST.get('water_ph', 0))
            water.save()
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Add user water profile error: {err}')
            messages.error(request, _(f'Add user water profile error'))
        return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))


class UserTrialRefusalView(LoginRequiredMixin, RedirectView):
    """
    User refusal trial
    """
    model = BrewUser
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        try:
            request.user.premium_trial = False
            request.user.save()
            send_tg_admins(user_trial_refusal.format(user=request.user.username))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse_lazy('main'))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Error of refusing a trial: {err}')
            messages.error(request, _(f'Error of refusing a trial'))
            return HttpResponseRedirect(reverse_lazy('main'))


class UserTrialActivateView(LoginRequiredMixin, RedirectView):
    """
    User activate trial
    """
    model = BrewUser
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            user.premium_trial = False
            user.status = PREMIUM
            end = datetime.today().date() + timedelta(days=30)
            user.premium_end = end
            user.limit_draft = 10
            user.save()
            messages.success(request, _(f'Trial period of premium access activated'))
            send_tg_admins(user_trial_activate.format(user=user.username,
                                                      date=end))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse_lazy('main'))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Error of refusing a trial: {err}')
            messages.error(request, _(f'Error of activate a trial'))
            return HttpResponseRedirect(reverse_lazy('main'))


class UserTelegramDeleteView(LoginRequiredMixin, UserPassesTestMixin, UserPathMixin, RedirectView):
    """
    Add device
    """
    model = BrewUser
    login_url = '/login/'

    def test_func(self):
        if self.request.user == self.get_object():
            return True
        else:
            messages.error(self.request, _(f'You cannot delete telegram profile'))
            return False

    def get(self, request, *args, **kwargs):
        try:
            usr = request.user
            tg_profile = get_object_or_404(UserTelegramProfile, user=usr.pk)
            tg_profile.enabled = False
            tg_profile.save()
            messages.success(request, _(f'Telegram profile deleted successfully'))
            action.send(self.request.user, verb=_(f'Telegram profile {tg_profile.user}: {tg_profile.user_tg_id} deleted'),
                        action_type=ACTION_DELETED,
                        description=_(f'User: {usr} deleted telegram '
                                      f'profile id: {tg_profile.user_tg_id}'),
                        target=tg_profile,
                        request=self.request)
        except Exception as err:
            logger.error(f'Error deleted telegram profile: {err}')
            messages.error(request, _(f'Error deleted telegram profile'))
        return HttpResponseRedirect(reverse_lazy('user_detail', args=[request.user]))


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, UserPathMixin, RedirectView):
    """
    Delete user
    """
    model = BrewUser
    login_url = '/login/'
    success_url = reverse_lazy('main')

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user.is_active = False
            if user.img:
                remove_thumbnails(user.img.path)
                remove_file(user.img.path)
            user.img = None
            user.save()
            for r in user.recipe_set.all():
                if r.status == STATUS_PUBLISHED:
                    usr = get_object_or_404(self.model, username=settings.DEFAULT_USER_ON_DELETE)
                    r.user = usr
                else:
                    r.status = STATUS_DELETE
                    remove_thumbnails(r.img.path)
                    remove_file(r.img.path)
                r.save()
            messages.success(request, _(f'User {user.username} successfully deleted'))
            action.send(self.request.user,
                        verb=_(f'User {user.username} self-deleted'),
                        action_type=ACTION_DELETED,
                        description=_(f'User {user.username} self-deleted'),
                        target=user,
                        request=self.request)
            send_tg_admins(user_deleted.format(login=user.username,
                                               email=user.email))
            logout(request)
        except Exception as err:
            logger.error(f'Error user delete: {err}')
            messages.error(request, _('Error user delete'))
        return HttpResponseRedirect(self.success_url)


class AdminMainView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    model = Recipe
    login_url = '/login/'
    template_name = 'admn/admn_dashboard.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stat'] = get_site_statistic()
        return context


class AdminModerationsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Recipe
    login_url = '/login/'
    template_name = 'admn/admn_recipes_mod.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_queryset(self):
        return self.model.objects.moderation()


class AdminRecipeView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, UpdateView):
    model = Recipe
    login_url = '/login/'
    form_class = RecipeForm
    context_object_name = 'recipe'
    template_name = 'admn/admn_recipe_one.html'
    success_url = reverse_lazy('admn_recipes_list')

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.object
        grain = recipe.grainingredients_set.all().order_by('-amount')
        grain_sum = grain.aggregate(Sum('amount'))['amount__sum']
        new = self.request.GET.get('new', '')
        value = self.request.GET.get('value', '')
        recalc = 1
        if new and value:
            if new == 'volume':
                recalc = float(value) / float(recipe.batch_size)
            elif new == 'weight':
                recalc = float(value) / float(grain_sum)
        misc = recipe.miscingredients_set.filter(use=USE_MASH)
        water = recipe.miscingredients_set.filter(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))
        mash = sorted(chain(grain,
                          recipe.fermentableingredients_set.filter(use=USE_MASH),
                          misc.exclude(Q(ingredient__type=ACIDS) | Q(ingredient__type=WATER_AGENT))),
                      key=lambda instance: instance.use,
                      reverse=False)
        boil = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_BOIL),
                            recipe.hopsingredients_set.filter(use=USE_BOIL),
                            recipe.miscingredients_set.filter(use=USE_BOIL)),
                      key=lambda instance: instance.time,
                      reverse=True)
        chilling = list(chain(recipe.fermentableingredients_set.filter(use=USE_HOP_STAND),
                             recipe.hopsingredients_set.filter(use=USE_HOP_STAND),
                             recipe.miscingredients_set.filter(use=USE_HOP_STAND)))
        dry_hop = sorted(chain(recipe.fermentableingredients_set.filter(use=USE_PRIMARY),
                             recipe.hopsingredients_set.filter(use=USE_PRIMARY),
                             recipe.miscingredients_set.filter(use=USE_PRIMARY)),
                         key=lambda instance: instance.time,
                         reverse=True)
        is_favorite = False
        if recipe.favorites.filter(id=self.request.user.id).exists():
            is_favorite = True
        _srm = int(recipe.srm)
        if _srm > 40:
            _srm = 41
        context['mash'] = mash
        context['water_salts'] = water
        context['boil'] = boil
        context['chilling'] = chilling
        context['dry_hop'] = dry_hop
        context['is_favorite'] = is_favorite
        context['grain_sum'] = grain_sum
        context['water_sum'] = recipe.mash_water + recipe.sparge_water
        context['hop_sum'] = recipe.hopsingredients_set.all().aggregate(Sum('amount'))['amount__sum']
        context['srm_color'] = SRM[_srm]
        context['recalc'] = recalc
        context['att'] = attenuation(recipe.OG, recipe.FG)
        context['stat'] = [STATUS_CHOICES[STATUS_DRAFT],
                           STATUS_CHOICES[STATUS_MODERATION],
                           STATUS_CHOICES[STATUS_PUBLISHED]]
        return context

    def post(self, request, *args, **kwargs):
        msg = ''
        self.object = self.get_object()
        match_style = request.POST.get('match_style', 'false')
        сonformity = request.POST.get('сonformity', '')
        status = request.POST.get('status', '')
        old_сonformity = self.object.сonformity
        old_status = self.object.status
        old_match_style = self.object.matches_style
        if сonformity:
            try:
                self.object.сonformity = int(сonformity)
                if status:
                    self.object.status = int(status)
                else:
                    self.object.status = STATUS_PUBLISHED
                if match_style == 'true':
                    self.object.matches_style = True
                else:
                    self.object.matches_style = False
                self.object.private = False
                self.object.seo_title = request.POST.get('seo_title', '')
                self.object.seo_description = request.POST.get('seo_description', '')
                self.object.seo_keywords = request.POST.get('seo_keywords', '')
                self.object.save()
                messages.success(self.request, _('Recipe status and сonformity changed successfully'))
                action.send(self.request.user,
                            verb=f'Status or сonformity Recipe: {self.object.name}',
                            action_type=ACTION_UPDATED,
                            description=f'User {request.user.username} update:\n'
                                        f'сonformity from {STATUS_CONFORMITY[old_сonformity][1]} to {STATUS_CONFORMITY[int(сonformity)][1]}\n'
                                        f'status from {STATUS_CHOICES[old_status][1]} to {STATUS_CHOICES[self.object.status][1]}\n'
                                        f'match in style {old_match_style} to {self.object.matches_style}\n',
                            target=self.object,
                            request=self.request)
                if old_status != self.object.status and self.object.status == STATUS_PUBLISHED:
                    self.object.public_date = now()
                    self.object.save()
                    style = ''
                    if self.object.style:
                        style = self.object.style
                    send_tg_users(recipe_on_publication.format(user=self.object.user,
                                                               style=style,
                                                               conf=STATUS_CONFORMITY[self.object.сonformity][1],
                                                               url=self.object.get_full_short_link(),
                                                               name=self.object.name))
            except Exception as err:
                logger.error(f'Recipe status and сonformity changed error: {err} - {msg}')
                messages.error(request, _(f'Recipe status and сonformity changed error'))
        return HttpResponseRedirect(self.success_url)


class AdminRecipeRefusionView(UserPassesTestMixin, GetObjectMixin, RedirectView):
    """
    Refusion publication recipe
    """
    model = Recipe
    success_url = reverse_lazy('admn_moderations')

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            recipient = self.object.user
            sender = request.user
            body = request.POST.get('message', '')
            if recipient != sender:
                msg = Message()
                msg.subject = _(f'Refusal to publish a recipe: {self.object.name}')
                msg.ip = request.META['REMOTE_ADDR']
                msg.user_agent = request.META['HTTP_USER_AGENT']
                msg.body = body
                msg.sender = sender
                msg.recipient = recipient
                msg.sent_at = now()
                msg.save()
            self.object.status = STATUS_DRAFT
            self.object.save()
            messages.success(request, _(f'Refusal to publish a recipe: {self.object.name}'))
            action.send(self.request.user,
                        verb=f'Refusal to publish a recipe: {self.object.name}',
                        action_type=ACTION_UPDATED,
                        description=f'User {request.user.username} rejection reason:\n'
                                    f'{body}',
                        target=self.object,
                        request=self.request)
        except Exception as err:
            logger.error(f'Error refusal to publish: {err}')
            messages.error(request, _(f'Error refusal to publish'))
        return HttpResponseRedirect(self.success_url)


class AdminRecipesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Recipe
    login_url = '/login/'
    paginate_by = 40
    template_name = 'admn/admn_recipes.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_queryset(self):
        qs = Q(status=STATUS_PUBLISHED) | Q(status=STATUS_STICKY) | Q(status=STATUS_DRAFT) \
             | Q(status=STATUS_MODERATION) | Q(status=STATUS_LOCKED)
        recipes = Recipe.objects.filter(qs)
        status = self.request.GET.get('filter', '')
        search = self.request.GET.get('search', '')
        order = self.request.GET.get('order_by', '-created_date')
        if search:
            new_context = recipes.filter(name__icontains=search).order_by(order)
        else:
            if status:
                new_context = recipes.filter(status=status).order_by(order)
            else:
                new_context = recipes.order_by(order)
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = (STATUS_CHOICES[STATUS_DRAFT],
                  STATUS_CHOICES[STATUS_MODERATION],
                  STATUS_CHOICES[STATUS_PUBLISHED],)
        context['status'] = status
        return context


class AdminUsersListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BrewUser
    login_url = '/login/'
    paginate_by = 40
    template_name = 'admn/admn_users.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_queryset(self):
        qs = self.model.objects.filter(is_confirm=True, is_active=True)
        if self.request.user.status < ADMIN:
            qs = qs.exclude(status=ADMIN)
        status = self.request.GET.get('filter', '')
        search = self.request.GET.get('search', '')
        order = self.request.GET.get('order_by', 'username')
        if search:
            new_context = qs.filter(username__icontains=search).order_by(order)
        else:
            if status:
                new_context = qs.filter(status=status).order_by(order)
            else:
                new_context = qs.order_by(order)
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = self.model.objects.filter(is_confirm=True, is_active=True)
        if self.request.user.status < ADMIN:
            qs = qs.exclude(status=ADMIN)
            status = STATUS_USER[:-1]
        else:
            status = STATUS_USER
        context['status'] = status
        context['users_count'] = qs.count()
        return context


class AdminUserView(LoginRequiredMixin, UserPassesTestMixin, UserPathMixin, UpdateView):
    model = BrewUser
    login_url = '/login/'
    form_class = UserForm
    template_name = 'admn/admn_user_one.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        limit_draft = self.request.POST.get('limit_draft', '')
        limit_device = self.request.POST.get('limit_device', '')
        limit_records = self.request.POST.get('records_limit', '')
        status = self.request.POST.get('status', '')
        premium_end = self.request.POST.get('premium_end', '')
        editor = request.POST.get('editor', False)
        if editor == 'on':
            if self.object.editor is False:
                self.object.editor = True
                messages.success(self.request, _('Open access to the user to add ingredients'))
                action.send(self.request.user,
                            verb=f'{self.object.username} - changed the ability to add ingredients',
                            action_type=ACTION_UPDATED,
                            description=f'{request.user.username} allowed'
                                        f' user {self.object.username} to add ingredients',
                            target=self.object,
                            request=self.request)
        else:
            if self.object.editor is True:
                self.object.editor = False
                messages.success(self.request, _('Access to the user to add ingredients is denied'))
                action.send(self.request.user,
                            verb=f'{self.object.username} - changed the ability to add ingredients',
                            action_type=ACTION_UPDATED,
                            description=f'{request.user.username} forbids'
                                        f' user {self.object.username} to add ingredients',
                            target=self.object,
                            request=self.request)
        self.object.save()
        if limit_draft and int(limit_draft) != self.object.limit_draft:
            try:
                old_limit = self.object.limit_draft
                self.object.limit_draft = int(limit_draft)
                self.object.save()
                messages.success(self.request, _('Draft limit changed'))
                action.send(self.request.user,
                            verb=f'{self.object.username} draft limit',
                            action_type=ACTION_UPDATED,
                            description=f'User {request.user.username} update '
                                        f'the draft limit for user {self.object.username} '
                                        f'from {old_limit} to {int(limit_draft)}',
                            target=self.object,
                            request=self.request)
            except Exception as err:
                messages.error(request, _(f'Error of changing the draft limit'))
        if limit_device and int(limit_device) != self.object.limit_device:
            try:
                old_limit = self.object.limit_device
                self.object.limit_device = int(limit_device)
                self.object.save()
                messages.success(self.request, _('Device limit changed'))
                action.send(self.request.user,
                            verb=f'{self.object.username} device limit',
                            action_type=ACTION_UPDATED,
                            description=f'User {request.user.username} update '
                                        f'the device limit for user {self.object.username} '
                                        f'from {old_limit} to {int(limit_device)}',
                            target=self.object,
                            request=self.request)
            except Exception as err:
                messages.error(request, _(f'Error of changing the device limit'))
        if limit_records and int(limit_records) != self.object.records_limit:
            try:
                old_limit = self.object.records_limit
                self.object.records_limit = int(limit_records)
                self.object.save()
                messages.success(self.request, _('Record limit changed'))
                action.send(self.request.user,
                            verb=f'{self.object.username} record limit',
                            action_type=ACTION_UPDATED,
                            description=f'User {request.user.username} update '
                                        f'the record limit for user {self.object.username} '
                                        f'from {old_limit} to {int(limit_records)}',
                            target=self.object,
                            request=self.request)
            except Exception as err:
                messages.error(request, _(f'Error of changing the record limit'))
        if status and int(status) != self.object.status:
            try:
                old_status = self.object.status
                self.object.status = int(status)
                if int(status) < 0:
                    self.object.is_active = False
                    ## todo При бане убирать устройства, рецепты черновики и телеграмм
                if old_status < 0 and int(status) >= 0:
                    self.object.is_active = True
                self.object.save()
                messages.success(self.request, _('User status changed'))
                action.send(self.request.user,
                            verb=f'\"{self.object.username}\" status',
                            action_type=ACTION_UPDATED,
                            description=f'User \"{request.user.username}\" update '
                                        f'user status for \"{self.object.username}\" '
                                        f'from \"{STATUS_USER[old_status + 1][1]}\" '
                                        f'to \"{STATUS_USER[int(status) + 1][1]}\"',
                            target=self.object,
                            request=self.request)
            except Exception as err:
                logger.error(f'Error user status changed: {err}')
                messages.error(request, _(f'Error user status changed'))
        if premium_end and self.object.status == PREMIUM:
            if self.object.premium_end is not None:
                old_premium_end = self.object.premium_end.strftime("%d.%m.%Y")
            else:
                old_premium_end = 'Null'
            new_premium_end = datetime.strptime(premium_end, "%d.%m.%Y").date()
            if self.object.premium_end != new_premium_end:
                try:
                    self.object.premium_end = new_premium_end
                    self.object.save()
                    messages.success(self.request, _('User Premium expiration date changed'))
                    action.send(self.request.user,
                                verb=f'\"{self.object.username}\" Premium expiration date',
                                action_type=ACTION_UPDATED,
                                description=f'User \"{request.user.username}\" update '
                                            f'user Premium expiration date for \"{self.object.username}\" '
                                            f'from {old_premium_end} to {premium_end}',
                                target=self.object,
                                request=self.request)
                except Exception as err:
                    messages.error(request, _(f'Error change end date premium'))
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stat'] = STATUS_USER[:4]
        return context


class AdminDevicesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ConnectedDevice
    login_url = '/login/'
    paginate_by = 40
    template_name = 'admn/admn_devices.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_queryset(self):
        qs = ConnectedDevice.objects.filter(enabled=True)
        order = self.request.GET.get('order_by', 'name')
        return qs.order_by(order)


class AdminDevicesRawDataView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = DeviceRawData
    login_url = '/login/'
    paginate_by = 80
    template_name = 'admn/admn_devices_raw.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_queryset(self):
        return self.model.objects.all()


class AdminActionsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Action
    login_url = '/login/'
    paginate_by = 40
    template_name = 'admn/admn_actions.html'

    def test_func(self):
        if self.request.user.is_admin:
            return True
        else:
            return False

    def get_queryset(self):
        qs = self.model.objects.all()
        action = self.request.GET.get('filter', '')
        order = self.request.GET.get('order_by', '-timestamp')
        if action:
            new_context = qs.filter(action_type=action).order_by(order)
        else:
            new_context = qs.order_by(order)
        return new_context


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = ACTION_CHOICES
        return context


class AdminUserBanView(LoginRequiredMixin, UserPassesTestMixin, UserPathMixin, RedirectView):
    """
    Ban user
    """
    model = BrewUser
    login_url = '/login/'
    success_url = reverse_lazy('admn_users_list')

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user.is_active = False
            user.is_banned = True
            if user.img:
                remove_thumbnails(user.img.path)
                remove_file(user.img.path)
                user.img = None
            pics = user.allpics
            if pics:
                for p in pics:
                    p.delete()
            user.save()
            for r in user.recipe_set.all():
                if r.status == STATUS_PUBLISHED:
                    usr = get_object_or_404(self.model, username=settings.DEFAULT_USER_ON_DELETE)
                    r.user = usr
                else:
                    r.status = STATUS_DELETE
                    remove_thumbnails(r.img.path)
                    remove_file(r.img.path)
                    r.img = None
                    pics = r.allpics
                    if pics:
                        for p in pics:
                            p.delete()
                r.save()
            messages.success(request, _(f'User {user.username} banned'))
            action.send(self.request.user,
                        verb=_(f'User {user.username} banned'),
                        action_type=ACTION_DELETED,
                        description=_(f'User {self.request.user.username} has banned {user.username}'),
                        target=user,
                        request=self.request)
            send_tg_admins(user_banned.format(mod=self.request.user,
                                              login=user.username,
                                              email=user.email))
        except Exception as err:
            logger.error(f'Error user delete: {err}')
            messages.error(request, _('Error user delete'))
        return HttpResponseRedirect(self.success_url)


class AdminSoulsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BrewUser
    login_url = '/login/'
    paginate_by = 40
    template_name = 'admn/admn_souls.html'

    def test_func(self):
        if self.request.user.is_moderator:
            return True
        else:
            return False

    def get_queryset(self):
        qs = self.model.objects.filter(is_active=False)
        status = self.request.GET.get('filter', '')
        search = self.request.GET.get('search', '')
        order = self.request.GET.get('order_by', 'username')
        if search:
            new_context = qs.filter(username__icontains=search).order_by(order)
        else:
            if status:
                new_context = qs.filter(status=status).order_by(order)
            else:
                new_context = qs.order_by(order)
        return new_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['souls_count'] = self.model.objects.filter(is_confirm=True, is_active=False).count()
        return context


class ComputingBrewView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'computing/comp_base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grain = list(chain(Malt.objects.all().order_by('name'), Fermentable.objects.all().order_by('name')))
        context['grains'] = grain
        context['styles'] = BeerStyle.objects.filter(guides=DEFAULT_GUIDES).order_by('name')
        context['yeast'] = Yeasts.objects.all().order_by('company', 'short_name')
        context['types'] = TYPE_BEER
        return context


class ComputingRecipeView(LoginRequiredMixin, TemplateView):
    """
    Create recipe
    """
    model = Recipe
    login_url = '/login/'
    template_name = 'computing/comp_recipe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.request.GET.get('recipe', None)
        if slug is not None:
            try:
                recipe = self.model.objects.get(slug=slug)
                context['recipe'] = recipe
                hs = recipe.hopsingredients_set.filter(use=USE_HOP_STAND).first()
                context['hs'] = hs
                qs = Q(use=USE_BOIL) | Q(use=USE_HOP_STAND)
                context['hops_ingredients'] = recipe.hopsingredients_set.filter(qs)
            except:
                pass
        context['types'] = TYPE_BEER
        context['styles'] = BeerStyle.objects.filter(guides=DEFAULT_GUIDES).order_by('name')
        context['grains'] = Malt.objects.all().order_by('company', 'name')
        context['ferms'] = Fermentable.objects.all().order_by('company', 'name')
        context['hops'] = Hops.objects.all()
        context['yeast'] = Yeasts.objects.all().order_by('company', 'short_name')
        return context


class ComputingRecipeSaveView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Save recipe
    """
    model = Recipe
    login_url = '/login/'

    def test_func(self):
        if self.request.user.ability_to_add:
            return True
        else:
            messages.error(self.request, _('Drafts limit is over'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            rcp = request.POST.get('recipe', '')
            if rcp:
                try:
                    recipe = self.model.objects.get(pk=int(rcp))
                    gr = recipe.grainingredients_set.all()
                    gr.delete()
                    fr = recipe.fermentableingredients_set.all()
                    fr.delete()
                    hp = recipe.hopsingredients_set.all()
                    hp.delete()
                    yt = recipe.yeastsingredients_set.all()
                    yt.delete()
                except ObjectDoesNotExist:
                    rcp = ''
            if not rcp:
                recipe = self.model()
                recipe.user = request.user
                index = request.POST.get('style_index', '')
                recipe_name = ''
                if index:
                    style = BeerStyle.objects.get(index=index, guides=DEFAULT_GUIDES)
                    recipe.style = style
                    recipe_name = style.name
                recipe.name = f'{STATUS_CHOICES[STATUS_DRAFT][1]}: {recipe_name}'
            recipe.batch_size = float(request.POST.get('batch_size', 0))
            recipe.mash_water = float(request.POST.get('mash_water', 0))
            recipe.sparge_water = float(request.POST.get('sparge_water', 0))
            recipe.pre_boil_size = float(request.POST.get('pre_boil_size', 0))
            recipe.fermentation_size = float(request.POST.get('fermentation_size', 0))
            recipe.boil_time = float(request.POST.get('boil_time', 60))
            recipe.efficiency_mash = float(request.POST.get('efficiency', 0))
            recipe.sediment_after_boil = float(request.POST.get('sediment', 0))
            recipe.PBG = float(request.POST.get('PBG', 1.0))
            recipe.OG = float(request.POST.get('OG', 1.0))
            recipe.FG = float(request.POST.get('FG', 1.0))
            recipe.abv = float(request.POST.get('abv', 0))
            recipe.ibu = float(request.POST.get('ibu', 0))
            recipe.srm = float(request.POST.get('srm', 0))
            recipe.save()
            grains = int(request.POST.get('grain_TOTAL_FORMS', 1))
            for g in range(1, grains + 1):
                gn = request.POST.get(f'grain_color_{g}')
                gn = int(gn.split('-')[2])
                grain = Malt.objects.get(pk=gn)
                grain_amount = float(is_none(request.POST.get(f'grain_amount_{g}', '')))
                ingredient = GrainIngredients()
                ingredient.recipe = recipe
                ingredient.ingredient = grain
                ingredient.amount = grain_amount
                ingredient.save()
            ferms = int(request.POST.get('ferm_TOTAL_FORMS', 1))
            for f in range(1, ferms + 1):
                fn = request.POST.get(f'ferm_extract_{f}')
                fn = int(fn.split('-')[1])
                ferm = Fermentable.objects.get(pk=fn)
                ferm_amount = float(is_none(request.POST.get(f'ferm_amount_{f}')))
                ingredient = FermentableIngredients()
                ingredient.recipe = recipe
                ingredient.ingredient = ferm
                ingredient.amount = ferm_amount
                ingredient.measure = KILOGRAM
                ingredient.use = USE_BOIL
                ingredient.save()
            hops = int(request.POST.get('hop_TOTAL_FORMS', 1))
            for h in range(1, hops + 1):
                hn = request.POST.get(f'hop_name_{h}', '')
                if hn:
                    hop = Hops.objects.get(pk=int(hn))
                    hop_ing = HopsIngredients()
                    hop_ing.recipe = recipe
                    hop_ing.ingredient = hop
                    hop_ing.amount = float(is_none(request.POST.get(f'hop_amount_{h}', 0)))
                    hop_ing.alfa = float(is_none(request.POST.get(f'hop_alfa_{h}', 0)))
                    use = int(request.POST.get(f'hop_use_{h}'))
                    if use == 2:
                        hop_ing.use = USE_HOP_STAND
                        hop_ing.time = int(request.POST.get('ibu_hstime'))
                        hop_ing.temp = int(request.POST.get('ibu_hstemp'))
                    else:
                        hop_ing.time = int(request.POST.get(f'hop_time_{h}', 77))
                        hop_ing.use = USE_BOIL
                    hop_ing.save()
            yst = request.POST.get('select-yeast', 0)
            if yst:
                yst = Yeasts.objects.get(pk=int(yst))
                yeast = YeastsIngredients()
                yeast.recipe = recipe
                yeast.ingredient = yst
                yeast.amount = 0
                yeast.save()
            return HttpResponseRedirect(reverse_lazy('recipe_edit', args=[recipe.slug]))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Save recipe error: {err}')
            messages.error(request, _(f'Save recipe error'))
            return HttpResponseRedirect(reverse_lazy('create_recipe', kwargs={'recipe': recipe.slug}))


class ComputingOtherView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'computing/comp_other.html'


class ComputingWaterView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    login_url = '/login/'
    template_name = 'computing/comp_water.html'

    def test_func(self):
        if self.request.user.is_pro:
            return True
        else:
            return False

    def handle_no_permission(self):
        messages.error(self.request, _('This functionality is only for Users with Premium status'))
        return HttpResponseRedirect(reverse_lazy('computing_main'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipes = list(chain(Recipe.objects.filter(status=STATUS_PUBLISHED).order_by('name'),
                             self.request.user.recipe_draft.order_by('name')))
        context['recipes'] = recipes
        context['waters'] = WaterProfile.objects.all()
        context['grains'] = Malt.objects.all().order_by('company', 'name')
        return context


class ComputingWaterSaveView(LoginRequiredMixin, RedirectView):
    """
    Save water agent in recipe
    """
    model = Recipe
    login_url = '/login/'

    def post(self, request, *args, **kwargs):  #TODO: Упростить. Проверку на 0
        try:
            recipe_id = request.POST.get('recipe_id', '')
            if not recipe_id:
                raise ObjectDoesNotExist
            recipe = self.model.objects.get(pk=int(recipe_id))
            op = getattr(recipe, 'wateroriginalprofile', None)
            if op is not None:
                recipe.wateroriginalprofile.delete()
            tp = getattr(recipe, 'watertargetprofile', None)
            if tp is not None:
                recipe.watertargetprofile.delete()
            if recipe.wateringredient_set.all():
                wis = recipe.wateringredient_set.all()
                wis.delete()
            wop = WaterOriginalProfile()
            wop.recipe = recipe
            wop.calcum = int(request.POST.get('original_profile_ca', '0'))
            wop.magnesium = int(request.POST.get('original_profile_mg', '0'))
            wop.sodium = int(request.POST.get('original_profile_na', '0'))
            wop.sulfate = int(request.POST.get('original_profile_so', '0'))
            wop.chloride = int(request.POST.get('original_profile_cl', '0'))
            wop.bicarbonate = int(request.POST.get('original_profile_hco', '0'))
            wop.ph = float(request.POST.get('original_profile_ph', '0'))
            wop.save()
            wtp = WaterTargetProfile()
            wtp.recipe = recipe
            wtp.calcum = int(request.POST.get('final_profile_ca', '0'))
            wtp.magnesium = int(request.POST.get('final_profile_mg', '0'))
            wtp.sodium = int(request.POST.get('final_profile_na', '0'))
            wtp.sulfate = int(request.POST.get('final_profile_so', '0'))
            wtp.chloride = int(request.POST.get('final_profile_cl', '0'))
            wtp.bicarbonate = int(request.POST.get('final_profile_hco', '0'))
            wtp.ph = float(request.POST.get('final_profile_ph', '0'))
            wtp.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_GYPSUM
            wi.amount_mash = float(request.POST.get('add_mash_caso', '0'))
            wi.amount_sparge = float(request.POST.get('add_sparge_caso', '0'))
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_CALCIUM_CHLORIDE
            wi.amount_mash = float(request.POST.get('add_mash_cacl', '0'))
            wi.amount_sparge = float(request.POST.get('add_sparge_cacl', '0'))
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_EPSOM
            wi.amount_mash = float(request.POST.get('add_mash_mgso', '0'))
            wi.amount_sparge = float(request.POST.get('add_sparge_mgso', '0'))
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_MAGNESIUM_CHLORIDE
            wi.amount_mash = float(request.POST.get('add_mash_mgcl', '0'))
            wi.amount_sparge = float(request.POST.get('add_sparge_mgcl', '0'))
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_CANNING_SALT
            wi.amount_mash = float(request.POST.get('add_mash_nacl', '0'))
            wi.amount_sparge = float(request.POST.get('add_sparge_nacl', '0'))
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_BAKING_SODA
            wi.amount_mash = float(request.POST.get('add_mash_nahco', '0'))
            wi.amount_sparge = 0
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_CHALK
            wi.amount_mash = float(request.POST.get('add_mash_caco', '0'))
            wi.amount_sparge = 0
            wi.save()
            wi = WaterIngredient()
            wi.recipe = recipe
            wi.additive = WATER_ADD_PICKLING_LIME
            wi.amount_mash = float(request.POST.get('add_mash_caoh', '0'))
            wi.amount_sparge = 0
            wi.save()
            acid = {'Молочная кислота': WATER_ADD_LACTIC_ACID,
                    'Фосфорная кислота': WATER_ADD_PHOSPHORIC_ACID,
                    'Уксусная кислота': WATER_ADD_ACETIC_ACID,
                    'Лимонная кислота': WATER_ADD_CITRIC_ACID}
            mash_acid = request.POST.get('recipe_mash_acid', 0)
            sparge_acid = request.POST.get('recipe_sparge_acid', 0)
            if mash_acid == sparge_acid:
                if acid.get(mash_acid):
                    wi = WaterIngredient()
                    wi.recipe = recipe
                    wi.additive = acid.get(mash_acid)
                    wi.amount_mash = float(request.POST.get('recipe_mash_acid_amount', '0'))
                    wi.amount_sparge = float(request.POST.get('recipe_sparge_acid_amount', '0'))
                    wi.save()
            if acid.get(mash_acid):
                wi = WaterIngredient()
                wi.recipe = recipe
                wi.additive = acid.get(mash_acid)
                wi.amount_mash = float(request.POST.get('recipe_mash_acid_amount', '0'))
                wi.amount_sparge = 0
                wi.save()
            if acid.get(sparge_acid):
                wi = WaterIngredient()
                wi.recipe = recipe
                wi.additive = acid.get(sparge_acid)
                wi.amount_mash = 0
                wi.amount_sparge = float(request.POST.get('recipe_sparge_acid_amount', '0'))
                wi.save()
            return HttpResponseRedirect(reverse_lazy('recipe_edit', args=[recipe.slug]))
        except ObjectDoesNotExist as err:
            logger.error(f'Recipe does not exist: {err}')
            messages.error(request, _(f'Recipe does not exist'))
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Add water agent in recipe error: {err}')
            messages.error(request, _(f'Add water agent in recipe error'))
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class DeviceInfoView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    User device info
    """
    model = ConnectedDevice
    login_url = '/login/'
    context_object_name = 'device'
    template_name = 'telemetry/telemetry.html'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user or self.request.user.is_admin:
            return True
        else:
            return False

    def get_object(self):
        return get_object_or_404(self.model, token=self.kwargs['token'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = self.get_object()
        context['log_data'] = device.devicedatalog_set.all().order_by('-created_date')[:100]
        return context


class ModulesListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Models list
    """
    model = ConnectedDevice
    login_url = '/login/'
    context_object_name = 'device'
    template_name = 'telemetry/modules_list.html'

    def test_func(self):
        if self.request.user.module_available:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modes = {}
        for m in MODULE_OPERATION_MODE:
            modes[m[0]] = m[1]
        context['modes'] = modes
        return context


class EquipmentsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Equipment list
    """
    model = ConnectedDevice
    login_url = '/login/'
    context_object_name = 'device'
    template_name = 'telemetry/equipments_list.html'

    def test_func(self):
        if self.request.user.module_available:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_equipment'] = EQUIPMENT_TYPE
        return context


class EquipmentsHelpView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Equipment Help page
    """
    login_url = '/login/'
    template_name = 'telemetry/equipments_help.html'

    def test_func(self):
        if self.request.user.module_available:
            return True
        else:
            return False


class EquipmentAddView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Add equipment
    """
    model = EquipmentModules
    login_url = '/login/'
    success_url = reverse_lazy('equipments_list')

    def test_func(self):
        if self.request.user.equipment_available:
            return True
        else:
            messages.error(self.request, _('Equipment limit is over'))
            return False

    def post(self, request, *args, **kwargs):
        try:
            equipment = self.model()
            equipment.user = request.user
            name = request.POST.get('name', '')
            eq_type = request.POST.get('type', EQUIPMENT_FERMENTER)
            if not name:
                name = EQUIPMENT_TYPE[eq_type]
            equipment.name = name
            equipment.type = eq_type
            equipment.save()
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Add equipment error: {err}')
            messages.error(request, _(f'Add equipment error'))
        return HttpResponseRedirect(self.success_url)


class EquipmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Delete equipment
    """
    model = EquipmentModules
    login_url = '/login/'
    success_url = reverse_lazy('equipments_list')

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user:
            return True
        else:
            messages.error(self.request, _('Equipment limit is over'))
            return False

    def get_object(self):
        return get_object_or_404(self.model, id=self.kwargs['object_id'])

    def get(self, request, *args, **kwargs):
        try:
            equipment = self.get_object()
            if equipment.main:
                main = equipment.main
                main.mode = MODULE_OM_NONE
                main.save()
            if equipment.second:
                second = equipment.second
                second.mode = MODULE_OM_NONE
                second.save()
            if equipment.third:
                third = equipment.third
                third.mode = MODULE_OM_NONE
                third.save()
            if equipment.fourth:
                fourth = equipment.fourth
                fourth.mode = MODULE_OM_NONE
                fourth.save()
            equipment.delete()
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Delete equipment error: {err}')
            messages.error(request, _(f'Delete equipment error'))
        return HttpResponseRedirect(self.success_url)



class EquipmentFermenterView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Equipment Fermenter control page
    """
    model = EquipmentModules
    login_url = '/login/'
    context_object_name = 'equipment'
    template_name = 'telemetry/equipment_fermenter.html'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user or self.request.user.is_admin:
            if self.object.main is not None:
                return True
            else:
                messages.error(self.request, _('Equipment not assembled'))
                return False
        else:
            return False

    def get_object(self):
        return get_object_or_404(self.model, id=self.kwargs['object_id'])


class EquipmentKettleView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Equipment Kettle control page
    """
    model = EquipmentModules
    login_url = '/login/'
    context_object_name = 'equipment'
    template_name = 'telemetry/equipment_kettle.html'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user or self.request.user.is_admin:
            if self.object.main is not None:
                return True
            else:
                messages.error(self.request, _('Equipment not assembled'))
                return False
        else:
            return False

    def get_object(self):
        return get_object_or_404(self.model, id=self.kwargs['object_id'])


class DeviceClearDataView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Device clear data
    """
    model = ConnectedDevice
    login_url = '/login/'

    def test_func(self):
        self.object = self.get_object()
        if self.request.user == self.object.user or self.request.user.is_admin:
            return True
        else:
            return False

    def get_object(self):
        return get_object_or_404(self.model, token=self.kwargs['token'])

    def get(self, request, *args, **kwargs):
        try:
            device = self.get_object()
            data = device.devicedatalog_set.all()
            data.delete()
        except Exception as err:
            logger.error(f'Error clear data on device {self.kwargs["token"]}: {err}')
            messages.error(request, _('Error clear data on device'))
        return HttpResponseRedirect(reverse_lazy('device_info', args=[device.token]))


class FeedbackView(RedirectView):
    """
    Send Feedback on Email
    """
    template_name = 'home/contacts.html'

    def post(self, request, *args, **kwargs):
        if self.request.recaptcha_is_valid:
            email_subject = 'Сообщение через форму Обратной связи'
            ctx = {
                'name': self.request.POST.get('name'),
                'email': self.request.POST.get('email'),
                'message': self.request.POST.get('message'),
            }
            email_body = render_to_string('registration/feedback_mail.txt', ctx)
            try:
                msg = EmailMessage(email_subject, email_body, to=[settings.EMAIL_HOST_USER])
                msg.send()
                send_tg_admins(feedback_message.format(name=ctx['name'],
                                                       email=ctx['email'],
                                                       ip=request.META.get('REMOTE_ADDR', ''),
                                                       body=ctx['message']))
                messages.success(self.request, _('Email sent'))
            except Exception as err:
                logger.error(f'Error send feedback: {err}')
                messages.error(self.request, _('Error send feedback'))
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


class AboutView(TemplateView):
    template_name = 'about_us.html'


class RegulationsView(TemplateView):
    template_name = 'regulations.html'


class TelegramBotWebhookView(View):
    # WARNING: if fail - Telegram webhook will be delivered again.
    # Can be fixed with async celery task execution
    def post(self, request, *args, **kwargs):
        if settings.DEBUG:
            process_telegram_event(json.loads(request.body))
        else:  # use celery in production
            process_telegram_event(json.loads(request.body))
            # process_telegram_event.delay(json.loads(request.body))

        # There is a great trick to send data in webhook response
        # e.g. remove buttons
        return JsonResponse({"ok": "POST request processed"})

    def get(self, request, *args, **kwargs):  # for debug
        return JsonResponse({"ok": "Get request processed. But nothing done"})


def csrf_failure(request, exception):
    return render(request, 'errors/404.html', status=404)


def page_not_found(request, exception):
    return render(request, 'errors/404.html', status=404)


def page_500_error(request):
    return render(request, 'errors/404.html', status=404)
