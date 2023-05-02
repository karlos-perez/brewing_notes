from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, RedirectView


from catalog.constants import CATEGORY_BASE_MALT, CATEGORY_CRYSTAL_MALT, CATEGORY_ROAST_MALT, CATEGORY_ACID_MALT, \
                              CATEGORY_WHEAT_MALT, UNMALTED, BASE_MALT
from catalog.models import Malt, Hops, Yeasts, Fermentable, Misc

from brew.constants import MEASURE

from .models import Pantry, MaltsReserve, FermentableReserve, HopsReserve, YeastsReserve, MiscReserve


class GetObjectPantryMixin(object):
    def get_object(self):
        return get_object_or_404(self.model, user__username=self.kwargs['username'])


class GetObjectIDMixin(object):
    def get_object(self):
        return get_object_or_404(self.model, id=self.kwargs['object_id'])


class ActivatePantryView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    """
    Activate pantry user
    """
    model = Pantry
    login_url = '/login/'

    def test_func(self):
        if self.request.user.is_pro:
            return True
        else:
            messages.error(self.request, _('Not enough rights'))
            return False

    def get_success_url(self):
        return reverse_lazy('user_detail', args=[self.request.user.username])

    def get(self, request, *args, **kwargs):
        obj, created = self.model.objects.get_or_create(user=self.request.user, enabled=True)
        if not created:
            messages.error(self.request, _('The pantry is already activated'))
            raise Http404
        else:
            if not obj.enabled:
                messages.error(self.request, _('The pantry is not enabled'))
                raise Http404
        return HttpResponseRedirect(self.get_success_url())


class PantryBalanceView(LoginRequiredMixin, UserPassesTestMixin,  GetObjectPantryMixin, DetailView):
    model = Pantry
    login_url = '/login/'
    context_object_name = 'pantry'
    template_name = 'pantry/pantry_balance.html'

    def test_func(self):
        obj = self.get_object()
        if obj.user == self.request.user and obj.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pantry = self.get_object()
        context['maltsreserve'] = pantry.maltsreserve_set.filter(spent=False)
        context['fermentablereserve'] = pantry.fermentablereserve_set.filter(spent=False)
        context['hopsreserve'] = pantry.hopsreserve_set.filter(spent=False)
        context['yeastsreserve'] = pantry.yeastsreserve_set.filter(spent=False)
        context['miscreserve'] = pantry.miscreserve_set.filter(spent=False)
        context['malts'] = Malt.objects.all().order_by('company', 'name')
        context['fermentable'] = Fermentable.objects.all().order_by('name')
        context['hops'] = Hops.objects.all().order_by('company', 'name')
        context['yeasts'] = Yeasts.objects.all().order_by('short_name', 'name')
        context['misc'] = Misc.objects.all().order_by('name')
        context['measure'] = MEASURE
        return context


class PantryWriteOffListView(LoginRequiredMixin, UserPassesTestMixin,  GetObjectPantryMixin, ListView):
    model = Pantry
    login_url = '/login/'
    context_object_name = 'pantry'
    template_name = 'pantry/pantry_writeoff.html'

    def test_func(self):
        obj = self.get_object()
        if obj.user == self.request.user and obj.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pantry = self.get_object()
        context['maltswriteoff'] = pantry.maltswriteoff_set.all()
        context['malts'] = pantry.maltsreserve_set.filter(spent=False)
        context['fermentablewriteoff'] = pantry.fermentablewriteoff_set.all()
        context['fermentables'] = pantry.fermentablereserve_set.filter(spent=False)
        context['hopswriteoff'] = pantry.hopswriteoff_set.all()
        context['hops'] = pantry.hopsreserve_set.filter(spent=False)
        context['yeastswriteoff'] = pantry.yeastswriteoff_set.all()
        context['yeasts'] = pantry.yeastsreserve_set.filter(spent=False)
        context['miscwriteoff'] = pantry.miscwriteoff_set.all()
        context['misc'] = pantry.miscreserve_set.filter(spent=False)
        context['recipes'] = self.request.user.recipe_draft.order_by('-created_date')
        return context


class MaltsListView(LoginRequiredMixin, UserPassesTestMixin, GetObjectPantryMixin, ListView):
    model = Pantry
    login_url = '/login/'
    template_name = 'pantry/pantry_malts_list.html'

    def test_func(self):
        obj = self.get_object()
        if obj.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_queryset(self):
        pantry = self.get_object()
        return pantry.maltsreserve_set.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pantry = self.get_object()
        malts_balance = pantry.maltsreserve_set.filter(spent=False)
        base = malts_balance.filter(malt__type=BASE_MALT)
        crystal = malts_balance.filter(malt__category=CATEGORY_CRYSTAL_MALT)
        roast = malts_balance.filter(malt__category=CATEGORY_ROAST_MALT)
        acid = malts_balance.filter(malt__category=CATEGORY_ACID_MALT)
        wheat = malts_balance.filter(malt__category=CATEGORY_WHEAT_MALT)
        unmalt = malts_balance.filter(malt__type=UNMALTED)
        context['base_malts'] = base.aggregate(Sum('balance'))['balance__sum']
        context['crystal_malts'] = crystal.aggregate(Sum('balance'))['balance__sum']
        context['roast_malts'] = roast.aggregate(Sum('balance'))['balance__sum']
        context['acid_malts'] = acid.aggregate(Sum('balance'))['balance__sum']
        context['wheat_malts'] = wheat.aggregate(Sum('balance'))['balance__sum']
        context['unmalted'] = unmalt.aggregate(Sum('balance'))['balance__sum']
        context['malts'] = Malt.objects.all().order_by('company', 'name')
        return context


class MaltOneView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, DetailView):
    model = MaltsReserve
    login_url = '/login/'
    context_object_name = 'box'
    template_name = 'pantry/pantry_malt_one.html'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['malts'] = Malt.objects.all().order_by('company', 'name')
        return context


class MaltEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, RedirectView):
    model = MaltsReserve
    login_url = '/login/'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy('pantry_malt_one', args=[obj.id])

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        malt_id = request.POST.get('malts', None)
        try:
            if malt_id is not None:
                malt = Malt.objects.get(pk=int(malt_id))
                obj.malt = malt
                parish = float(request.POST.get('malt_parish', 0))
                balance = float(request.POST.get('malt_balance', 0))
                if balance <= parish:
                    obj.parish = parish
                    obj.balance = balance
                    obj.cost_per_unit = float(request.POST.get('malt_cost_per_unit', 0))
                    obj.supplier = request.POST.get('malt_supplier', '')
                    obj.note = request.POST.get('malt_note', '')
                    dt = request.POST.get('malt_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    obj.created_date = date
                    obj.save()
                else:
                    messages.error(self.request, _('The amount of malt balance more parish'))
            else:
                raise
        except:
            messages.error(self.request, _('The error malt edit'))
        return HttpResponseRedirect(self.get_success_url())


class FermentablesListView(LoginRequiredMixin, UserPassesTestMixin, GetObjectPantryMixin, ListView):
    model = Pantry
    login_url = '/login/'
    template_name = 'pantry/pantry_fermentable_list.html'

    def test_func(self):
        obj = self.get_object()
        if obj.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_queryset(self):
        pantry = self.get_object()
        return pantry.fermentablereserve_set.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fermentable'] = Fermentable.objects.all().order_by('name')
        context['measure'] = MEASURE
        return context


class FermentableOneView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, DetailView):
    model = FermentableReserve
    login_url = '/login/'
    context_object_name = 'box'
    template_name = 'pantry/pantry_fermentable_one.html'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fermentable'] = Fermentable.objects.all().order_by('name')
        context['measure'] = MEASURE
        return context


class FermentableEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, RedirectView):
    model = FermentableReserve
    login_url = '/login/'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy('pantry_fermentable_one', args=[obj.id])

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        fermentable_id = request.POST.get('fermentables', None)
        try:
            if fermentable_id is not None:
                fermentable = Fermentable.objects.get(pk=int(fermentable_id))
                obj.fermentable = fermentable
                parish = float(request.POST.get('fermentable_parish', 0))
                balance = float(request.POST.get('fermentable_balance', 0))
                if balance <= parish:
                    obj.parish = parish
                    obj.balance = balance
                    obj.cost_per_unit = float(request.POST.get('fermentable_cost_per_unit', 0))
                    obj.supplier = request.POST.get('fermentable_supplier', '')
                    obj.note = request.POST.get('fermentable_note', '')
                    dt = request.POST.get('fermentable_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    obj.created_date = date
                    obj.save()
                else:
                    messages.error(self.request, _('The amount of fermentable balance more parish'))
            else:
                raise
        except:
            messages.error(self.request, _('The error fermentable edit'))
        return HttpResponseRedirect(self.get_success_url())


class HopsListView(LoginRequiredMixin, GetObjectPantryMixin, ListView):
    model = Pantry
    login_url = '/login/'
    template_name = 'pantry/pantry_hops_list.html'

    def get_queryset(self):
        pantry = self.get_object()
        return pantry.hopsreserve_set.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pantry = self.request.user.pantry
        hops_total = pantry.hopsreserve_set.filter(spent=False)
        context['hops_total'] = hops_total.aggregate(Sum('balance'))['balance__sum']
        context['hops'] = Hops.objects.all().order_by('company', 'name')
        return context


class HopOneView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, DetailView):
    model = HopsReserve
    login_url = '/login/'
    context_object_name = 'box'
    template_name = 'pantry/pantry_hop_one.html'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hops'] = Hops.objects.all().order_by('company', 'name')
        return context


class HopEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, RedirectView):
    model = HopsReserve
    login_url = '/login/'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy('pantry_hop_one', args=[obj.id])

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        hop_id = request.POST.get('hops', None)
        try:
            if hop_id is not None:
                hop = Hops.objects.get(pk=int(hop_id))
                obj.hop = hop
                obj.alfa = request.POST.get('hop_alfa', 0)
                parish = int(request.POST.get('hop_parish', 0))
                balance = int(request.POST.get('hop_balance', 0))
                if balance <= parish:
                    obj.parish = parish
                    obj.balance = balance
                    obj.cost_per_unit = float(request.POST.get('hop_cost_per_unit', 0))
                    obj.supplier = request.POST.get('hop_supplier', '')
                    obj.note = request.POST.get('hop_note', '')
                    dt = request.POST.get('hop_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    obj.created_date = date
                    obj.save()
                else:
                    messages.error(self.request, _('The amount of hop balance more parish'))
            else:
                raise
        except:
            messages.error(self.request, _('The error hop edit'))
        return HttpResponseRedirect(self.get_success_url())


class YeastsListView(LoginRequiredMixin, GetObjectPantryMixin, ListView):
    model = Pantry
    login_url = '/login/'
    template_name = 'pantry/pantry_yeasts_list.html'

    def get_queryset(self):
        pantry = self.get_object()
        return pantry.yeastsreserve_set.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['yeasts'] = Yeasts.objects.all().order_by('short_name', 'name')
        context['measure'] = MEASURE
        return context


class YeastOneView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, DetailView):
    model = YeastsReserve
    login_url = '/login/'
    context_object_name = 'box'
    template_name = 'pantry/pantry_yeast_one.html'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['yeasts'] = Yeasts.objects.all().order_by('short_name', 'name')
        context['measure'] = MEASURE
        return context


class YeastEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, RedirectView):
    model = YeastsReserve
    login_url = '/login/'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy('pantry_yeast_one', args=[obj.id])

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        yeast_id = request.POST.get('yeasts', None)
        try:
            if yeast_id is not None:
                yeast = Yeasts.objects.get(pk=int(yeast_id))
                obj.yeast = yeast
                obj.measure = request.POST.get('yeast_measure', 0)
                parish = float(request.POST.get('yeast_parish', 0))
                balance = float(request.POST.get('yeast_balance', 0))
                if balance <= parish:
                    obj.parish = parish
                    obj.balance = balance
                    obj.cost_per_unit = float(request.POST.get('yeast_cost_per_unit', 0))
                    obj.supplier = request.POST.get('yeast_supplier', '')
                    obj.note = request.POST.get('yeast_note', '')
                    created_date = request.POST.get('yeast_cr_date', '')
                    if created_date:
                        cr_date = datetime.strptime(created_date, "%d.%m.%Y").date()
                    else:
                        cr_date = None
                    obj.created_date = cr_date
                    expiration_date = request.POST.get('yeast_ex_date', '')
                    if expiration_date:
                        ex_date = datetime.strptime(expiration_date, "%d.%m.%Y").date()
                    else:
                        ex_date = None
                    obj.expiration_date = ex_date
                    obj.save()
                else:
                    messages.error(self.request, _('The amount of yeast balance more parish'))
            else:
                raise
        except Exception as err:
            messages.error(self.request, _('The error yeast edit'))
        return HttpResponseRedirect(self.get_success_url())


class MiscListView(LoginRequiredMixin, UserPassesTestMixin, GetObjectPantryMixin, ListView):
    model = Pantry
    login_url = '/login/'
    template_name = 'pantry/pantry_misc_list.html'

    def test_func(self):
        obj = self.get_object()
        if obj.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_queryset(self):
        pantry = self.get_object()
        return pantry.miscreserve_set.all().order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['misc'] = Misc.objects.all().order_by('name')
        context['measure'] = MEASURE
        return context


class MiscOneView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, DetailView):
    model = MiscReserve
    login_url = '/login/'
    context_object_name = 'box'
    template_name = 'pantry/pantry_misc_one.html'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['misc'] = Misc.objects.all().order_by('name')
        context['measure'] = MEASURE
        return context


class MiscEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectIDMixin, RedirectView):
    model = MiscReserve
    login_url = '/login/'

    def test_func(self):
        obj = self.get_object()
        if obj.pantry.user == self.request.user and self.request.user.available_pantry:
            return True
        else:
            return False

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy('pantry_misc_one', args=[obj.id])

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        misc_id = request.POST.get('misc', None)
        try:
            if misc_id is not None:
                misc = Misc.objects.get(pk=int(misc_id))
                obj.misc = misc
                parish = float(request.POST.get('misc_parish', 0))
                balance = float(request.POST.get('misc_balance', 0))
                if balance <= parish:
                    obj.parish = parish
                    obj.balance = balance
                    obj.cost_per_unit = float(request.POST.get('misc_cost_per_unit', 0))
                    obj.supplier = request.POST.get('misc_supplier', '')
                    obj.note = request.POST.get('misc_note', '')
                    dt = request.POST.get('misc_date', '')
                    if dt:
                        date = datetime.strptime(dt, "%d.%m.%Y").date()
                    else:
                        date = None
                    obj.created_date = date
                    obj.save()
                else:
                    messages.error(self.request, _(f'The amount of misc balance more parish'))
            else:
                raise
        except:
            messages.error(self.request, _('The error misc edit'))
        return HttpResponseRedirect(self.get_success_url())

