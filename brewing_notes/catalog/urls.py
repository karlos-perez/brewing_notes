from django.urls import path, re_path
from django.views.generic import RedirectView
from django.contrib.auth import views
from django.conf.urls import include

from .views import *


urlpatterns = [
    path('catalog/malts/', MaltListView.as_view(), name='malts_list'),
    path('catalog/malts/add/', MaltAddView.as_view(), name='malt_add'),
    path('catalog/malts/edit/<slug:slug>/', MaltEditView.as_view(), name='malt_edit'),
    path('catalog/malts/<slug:slug>/', MaltOneView.as_view(), name="malt_one"),
    path('catalog/fermentables/', FermListView.as_view(), name="ferms_list"),
    path('catalog/fermentables/add/', FermAddView.as_view(), name="ferm_add"),
    path('catalog/fermentables/edit/<slug:slug>/', FermEditView.as_view(), name='ferm_edit'),
    path('catalog/fermentables/<slug:slug>/', FermOneView.as_view(), name="ferm_one"),
    path('catalog/hops/', HopsListView.as_view(), name="hops_list"),
    path('catalog/hops/add/', HopsAddView.as_view(), name="hop_add"),
    path('catalog/hops/edit/<slug:slug>/', HopsEditView.as_view(), name="hop_edit"),
    path('catalog/hops/<slug:slug>/', HopsOneView.as_view(), name="hop_one"),
    path('catalog/yeasts/', YeastsListView.as_view(), name="yeasts_list"),
    path('catalog/yeasts/add/', YeastsAddView.as_view(), name="yeast_add"),
    path('catalog/yeasts/edit/<slug:slug>/', YeastsEditView.as_view(), name="yeast_edit"),
    path('catalog/yeasts/<slug:slug>/', YeastsOneView.as_view(), name="yeast_one"),
    path('catalog/misc/', MiscListView.as_view(), name="misc_list"),
    path('catalog/misc/add', MiscAddView.as_view(), name="misc_add"),
    path('catalog/misc/edit/<slug:slug>/', MiscEditView.as_view(), name='misc_edit'),
    path('catalog/misc/<slug:slug>/', MiscOneView.as_view(), name="misc_one"),
    path('catalog/waters/', WatersListView.as_view(), name="waters_list"),
    path('catalog/water/add/', WaterAddView.as_view(), name="water_add"),
    path('catalog/water/edit/<slug:slug>/', WaterEditView.as_view(), name="water_edit"),
    path('catalog/water/<slug:slug>/', WaterOneView.as_view(), name="water_one"),
    path('catalog/styles/', StylesListView.as_view(), name="styles_list"),
    path('catalog/styles/<slug:slug>/', StyleOneView.as_view(), name="style_one"),
    path('catalog/style/add/', StyleAddView.as_view(), name="style_add"),
    # path('catalog/styles/<slug:slug>', StyleView.as_view(), name="style_list"),


]
