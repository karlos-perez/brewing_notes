from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from nnmware.core.constants import ACTION_EDITED, ACTION_ADDED
from nnmware.core.signals import action

from .constants import TYPE_GRAIN, TYPE_FERMENTABLE, TYPE_HOPS, \
    TYPE_YEASTS, TYPE_ADDITIVE, TYPE_BEER, BEER_STYLE_GUIDELINES, BJCP_2021
from .forms import MaltAddForm, FermAddForm, HopsAddForm, YeastsAddForm, \
    MiscAddForm, WaterAddForm, StyleAddForm
from .models import Malt, Fermentable, Hops, Yeasts, Misc, BeerStyle, WaterProfile


DEFAULT_BJCP = BJCP_2021


class GetObjectMixin(object):
    def get_object(self):
        return get_object_or_404(self.model, slug=self.kwargs['slug'])


class ActionAddMixin(object):
    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        if hasattr(self, 'company'):
            company = self.company
        else:
            company = '---'
        action.send(self.request.user,
                    verb=f'{self.object._meta.verbose_name}: {self.object.name}',
                    action_type=ACTION_ADDED,
                    description=f'{self.object.name} | {company}',
                    target=self.object,
                    request=self.request)
        return HttpResponseRedirect(self.get_success_url())


class ActionEditMixin(object):
    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        if hasattr(self, 'company'):
            company = self.company
        else:
            company = '---'
        action.send(self.request.user,
                    verb=f'{self.object._meta.verbose_name}: {self.object.name}',
                    action_type=ACTION_EDITED,
                    description=f'{self.object.name} | {company}',
                    target=self.object,
                    request=self.request)
        return HttpResponseRedirect(self.get_success_url())


class ListMixin(LoginRequiredMixin):
    login_url = '/login/'
    paginate_by = 40

    def get_queryset(self):
        qs = self.model.objects.all()
        type_ing = self.request.GET.get('type', '')
        company = self.request.GET.get('company', '')
        order = self.request.GET.get('order_by', 'name')
        if type_ing and company:
            if company == 'empty':
                company = None
            new_qs = qs.filter(type=type_ing, company=company).order_by(order)
        elif type_ing:
            new_qs = qs.filter(type=type_ing).order_by(order)
        elif company:
            if company == 'empty':
                company = None
            new_qs = qs.filter(company=company).order_by(order)
        else:
            new_qs = qs.order_by(order)
        return new_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = self.type_
        context['all'] = self.model.objects.all()
        return context


class MaltListView(ListMixin, ListView):
    model = Malt
    template_name = 'catalog/malt_list.html'
    type_ = TYPE_GRAIN


class MaltAddView(LoginRequiredMixin, UserPassesTestMixin, ActionAddMixin, CreateView):
    model = Malt
    login_url = '/login/'
    form_class = MaltAddForm
    template_name = 'catalog/malt_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False


class MaltEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, ActionEditMixin, UpdateView):
    model = Malt
    login_url = '/login/'
    form_class = MaltAddForm
    template_name = 'catalog/malt_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False


class MaltOneView(LoginRequiredMixin, DetailView):
    model = Malt
    login_url = '/login/'
    context_object_name = 'malt'
    template_name = 'catalog/malt_one.html'


class FermListView(ListMixin, ListView):
    model = Fermentable
    template_name = 'catalog/ferm_list.html'
    type_ = TYPE_FERMENTABLE


class FermAddView(LoginRequiredMixin, UserPassesTestMixin, ActionAddMixin, CreateView):
    model = Fermentable
    login_url = '/login/'
    form_class = FermAddForm
    template_name = 'catalog/ferm_add.html'

    def test_func(self):
        if self.request.user.is_editor or self.request.user.is_moderator:
            return True
        else:
            return False


class FermEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, ActionEditMixin, UpdateView):
    model = Fermentable
    login_url = '/login/'
    form_class = FermAddForm
    template_name = 'catalog/ferm_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False


class FermOneView(LoginRequiredMixin, DetailView):
    model = Fermentable
    login_url = '/login/'
    context_object_name = 'ferm'
    template_name = 'catalog/ferm_one.html'


class HopsListView(ListMixin, ListView):
    model = Hops
    template_name = 'catalog/hops_list.html'
    type_ = TYPE_HOPS


class HopsAddView(LoginRequiredMixin, UserPassesTestMixin, ActionAddMixin, CreateView):
    model = Hops
    login_url = '/login/'
    form_class = HopsAddForm
    template_name = 'catalog/hop_add.html'

    def test_func(self):
        if self.request.user.is_editor or self.request.user.is_moderator:
            return True
        else:
            return False


class HopsEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, ActionEditMixin, UpdateView):
    model = Hops
    login_url = '/login/'
    form_class = HopsAddForm
    template_name = 'catalog/hop_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))


class HopsOneView(LoginRequiredMixin, DetailView):
    model = Hops
    login_url = '/login/'
    context_object_name = 'hop'
    template_name = 'catalog/hops_one.html'


class YeastsListView(ListMixin, ListView):
    model = Yeasts
    template_name = 'catalog/yeasts_list.html'
    type_ = TYPE_YEASTS


class YeastsAddView(LoginRequiredMixin, UserPassesTestMixin, ActionAddMixin, CreateView):
    model = Yeasts
    login_url = '/login/'
    form_class = YeastsAddForm
    template_name = 'catalog/yeast_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False


class YeastsEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, ActionEditMixin, UpdateView):
    model = Yeasts
    login_url = '/login/'
    form_class = YeastsAddForm
    template_name = 'catalog/yeast_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))


class YeastsOneView(LoginRequiredMixin, DetailView):
    model = Yeasts
    login_url = '/login/'
    context_object_name = 'yeast'
    template_name = 'catalog/yeasts_one.html'


class MiscListView(ListMixin, ListView):
    model = Misc
    template_name = 'catalog/misc_list.html'
    type_ = TYPE_ADDITIVE


class MiscAddView(LoginRequiredMixin, UserPassesTestMixin, ActionAddMixin, CreateView):
    model = Misc
    login_url = '/login/'
    form_class = MiscAddForm
    template_name = 'catalog/misc_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False


class MiscEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, ActionEditMixin, UpdateView):
    model = Misc
    login_url = '/login/'
    form_class = MiscAddForm
    template_name = 'catalog/misc_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))


class MiscOneView(LoginRequiredMixin, DetailView):
    model = Misc
    login_url = '/login/'
    context_object_name = 'misc'
    template_name = 'catalog/misc_one.html'


class WatersListView(ListView):
    model = WaterProfile
    template_name = 'catalog/water_list.html'


class WaterAddView(LoginRequiredMixin, UserPassesTestMixin, ActionAddMixin, CreateView):
    model = WaterProfile
    login_url = '/login/'
    form_class = WaterAddForm
    template_name = 'catalog/water_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False


class WaterEditView(LoginRequiredMixin, UserPassesTestMixin, GetObjectMixin, ActionEditMixin, UpdateView):
    model = WaterProfile
    login_url = '/login/'
    form_class = WaterAddForm
    template_name = 'catalog/water_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))


class WaterOneView(LoginRequiredMixin, DetailView):
    model = WaterProfile
    login_url = '/login/'
    context_object_name = 'water'
    template_name = 'catalog/water_one.html'


class StylesListView(ListView):
    model = BeerStyle
    paginate_by = 40
    template_name = 'catalog/styles_list.html'

    def get_queryset(self):
        qs = self.model.objects.all()
        type_ing = self.request.GET.get('type', '')
        bjcp = self.request.GET.get('bjcp', '')
        order = self.request.GET.get('order_by', 'name')
        if type_ing and bjcp:
            new_qs = qs.filter(type=type_ing, guides=bjcp).order_by(order)
        elif type_ing:
            new_qs = qs.filter(type=type_ing).order_by(order)
        elif bjcp:
            new_qs = qs.filter(guides=bjcp).order_by(order)
        else:
            new_qs = qs.order_by(order)
        return new_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = TYPE_BEER
        context['bjcp'] = BEER_STYLE_GUIDELINES
        context['all'] = self.model.objects.all()
        return context


class StyleOneView(LoginRequiredMixin, DetailView):
    model = BeerStyle
    login_url = '/login/'
    context_object_name = 'style'
    template_name = 'catalog/style_one.html'


class StyleAddView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = BeerStyle
    login_url = '/login/'
    form_class = StyleAddForm
    template_name = 'catalog/style_add.html'

    def test_func(self):
        if self.request.user.is_editor:
            return True
        else:
            return False

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        action.send(self.request.user,
                    verb=f'{self.object._meta.verbose_name}: {self.object.name}',
                    action_type=ACTION_ADDED,
                    description=f'{self.object.name} | {self.object.guides}',
                    target=self.object,
                    request=self.request)
        return HttpResponseRedirect(self.get_success_url())





