from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DocsMainView(LoginRequiredMixin, TemplateView):
    """
    Documentation main page
    """
    login_url = '/login/'
    template_name = 'docs/docs_main.html'


class DocsBNaboutView(LoginRequiredMixin, TemplateView):
    """
    About BrewingNotes page
    """
    login_url = '/login/'
    template_name = 'docs/BrewingNotes/BN_about.html'


class DocsBNpremiumView(LoginRequiredMixin, TemplateView):
    """
    About Premium access page
    """
    login_url = '/login/'
    template_name = 'docs/BrewingNotes/BN_premium.html'


class DocsConnectionDevicesView(LoginRequiredMixin, TemplateView):
    """
    Connection devices page
    """
    login_url = '/login/'
    template_name = 'docs/setup_device.html'


class DocsBNCmoduleView(LoginRequiredMixin, TemplateView):
    """
    BNC module main page
    """
    login_url = '/login/'
    template_name = 'docs/BNC_module/BNCmodule.html'


class DocsBNCCreationView(LoginRequiredMixin, TemplateView):
    """
    Creations and configuration BNC module
    """
    login_url = '/login/'
    template_name = 'docs/BNC_module/BNCmodule_create_settings.html'


class DocsBNCEquipmentsView(LoginRequiredMixin, TemplateView):
    """
    Equipment list page
    """
    login_url = '/login/'
    template_name = 'docs/BNC_module/BNCmodule_equipment_list.html'


class DocsBNCEquipmentsCreateView(LoginRequiredMixin, TemplateView):
    """
    Equipment create page
    """
    login_url = '/login/'
    template_name = 'docs/BNC_module/BNCmodule_equipment_create.html'


class DocsBNCFermenterView(LoginRequiredMixin, TemplateView):
    """
    Fermenter page
    """
    login_url = '/login/'
    template_name = 'docs/BNC_module/BNCmodule_fermenter.html'


class DocsBNCKettleView(LoginRequiredMixin, TemplateView):
    """
    Kettle page
    """
    login_url = '/login/'
    template_name = 'docs/BNC_module/BNCmodule_kettle.html'

