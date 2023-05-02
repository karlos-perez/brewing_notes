from django.urls import path

from .views import *


urlpatterns = [
    path('docs', DocsMainView.as_view(), name='docs_main'),
    path('docs/BrewingNotes', DocsBNaboutView.as_view(), name='docs_bn_about'),
    path('docs/BrewingNotes/Premium', DocsBNpremiumView.as_view(), name='docs_bn_premium'),
    path('docs/connection/devices', DocsConnectionDevicesView.as_view(), name='docs_conn_devices'),
    path('docs/BNCmodule', DocsBNCmoduleView.as_view(), name='docs_bnc_module'),
    path('docs/BNCmodule/creation-and-configuration/', DocsBNCCreationView.as_view(), name='docs_bnc_creation'),
    path('docs/BNCmodule/equipments', DocsBNCEquipmentsView.as_view(), name='docs_bnc_equipments'),
    path('docs/BNCmodule/create-equipments', DocsBNCEquipmentsCreateView.as_view(), name='docs_bnc_equipments_create'),
    path('docs/BNCmodule/fermenter', DocsBNCFermenterView.as_view(), name='docs_bnc_fermenter'),
    path('docs/BNCmodule/kettle', DocsBNCKettleView.as_view(), name='docs_bnc_kettle'),
]