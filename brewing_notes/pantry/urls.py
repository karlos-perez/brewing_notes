from django.urls import path

from .ajax import *
from .views import *


urlpatterns = [
    path('pantry/activate/', ActivatePantryView.as_view(), name='pantry_activate'),
    path('pantry/<str:username>/balance/', PantryBalanceView.as_view(), name='pantry_balance'),
    path('pantry/<str:username>/write-off/', PantryWriteOffListView.as_view(), name='pantry_writeoff_list'),

    path('pantry/<str:username>/malts/', MaltsListView.as_view(), name='pantry_malts_list'),
    path('pantry/malt/<int:object_id>', MaltOneView.as_view(), name='pantry_malt_one'),
    path('pantry/malt/<int:object_id>/edit/', MaltEditView.as_view(), name='pantry_malt_edit'),

    path('pantry/<str:username>/fermentables/', FermentablesListView.as_view(), name='pantry_fermentables_list'),
    path('pantry/fermentable/<int:object_id>', FermentableOneView.as_view(), name='pantry_fermentable_one'),
    path('pantry/fermentable/<int:object_id>/edit/', FermentableEditView.as_view(), name='pantry_fermentable_edit'),

    path('pantry/<str:username>/hops/', HopsListView.as_view(), name='pantry_hops_list'),
    path('pantry/hop/<int:object_id>', HopOneView.as_view(), name='pantry_hop_one'),
    path('pantry/hop/<int:object_id>/edit/', HopEditView.as_view(), name='pantry_hop_edit'),

    path('pantry/<str:username>/yeasts/', YeastsListView.as_view(), name='pantry_yeasts_list'),
    path('pantry/yeast/<int:object_id>', YeastOneView.as_view(), name='pantry_yeast_one'),
    path('pantry/yeast/<int:object_id>/edit/', YeastEditView.as_view(), name='pantry_yeast_edit'),

    path('pantry/<str:username>/misc/', MiscListView.as_view(), name='pantry_misc_list'),
    path('pantry/misc/<int:object_id>', MiscOneView.as_view(), name='pantry_misc_one'),
    path('pantry/misc/<int:object_id>/edit/', MiscEditView.as_view(), name='pantry_misc_edit'),

    path('api/v1/pantry/<int:object_id>/parish/malt/add', pantry_parish_malt_add, name='pantry_parish_malt_add'),
    path('api/v1/pantry/<int:object_id>/parish/malt/delete', pantry_parish_malt_delete, name='pantry_parish_malt_delete'),
    path('api/v1/pantry/<int:object_id>/consumption/malt/add', pantry_consumption_malt_add, name='pantry_consumption_malt_add'),
    path('api/v1/pantry/<int:object_id>/consumption/malt/delete', pantry_consumption_malt_delete, name='pantry_consumption_malt_delete'),

    path('api/v1/pantry/<int:object_id>/parish/fermentable/add', pantry_parish_fermentable_add, name='pantry_parish_fermentable_add'),
    path('api/v1/pantry/<int:object_id>/parish/fermentable/delete', pantry_parish_fermentable_delete, name='pantry_parish_fermentable_delete'),
    path('api/v1/pantry/<int:object_id>/consumption/fermentable/add', pantry_consumption_fermentable_add, name='pantry_consumption_fermentable_add'),
    path('api/v1/pantry/<int:object_id>/consumption/fermentable/delete', pantry_consumption_fermentable_delete, name='pantry_consumption_fermentable_delete'),

    path('api/v1/pantry/<int:object_id>/parish/hop/add', pantry_parish_hop_add, name='pantry_parish_hop_add'),
    path('api/v1/pantry/<int:object_id>/parish/hop/delete', pantry_parish_hop_delete, name='pantry_parish_hop_delete'),
    path('api/v1/pantry/<int:object_id>/consumption/hop/add', pantry_consumption_hop_add, name='pantry_consumption_hop_add'),
    path('api/v1/pantry/<int:object_id>/consumption/hop/delete', pantry_consumption_hop_delete, name='pantry_consumption_hop_delete'),

    path('api/v1/pantry/<int:object_id>/parish/yeast/add', pantry_parish_yeast_add, name='pantry_parish_yeast_add'),
    path('api/v1/pantry/<int:object_id>/parish/yeast/delete', pantry_parish_yeast_delete, name='pantry_parish_yeast_delete'),
    path('api/v1/pantry/<int:object_id>/consumption/yeast/add', pantry_consumption_yeast_add, name='pantry_consumption_yeast_add'),
    path('api/v1/pantry/<int:object_id>/consumption/yeast/delete', pantry_consumption_yeast_delete, name='pantry_consumption_yeast_delete'),

    path('api/v1/pantry/<int:object_id>/parish/misc/add', pantry_parish_misc_add, name='pantry_parish_misc_add'),
    path('api/v1/pantry/<int:object_id>/parish/misc/delete', pantry_parish_misc_delete, name='pantry_parish_misc_delete'),
    path('api/v1/pantry/<int:object_id>/consumption/misc/add', pantry_consumption_misc_add, name='pantry_consumption_misc_add'),
    path('api/v1/pantry/<int:object_id>/consumption/misc/delete', pantry_consumption_misc_delete, name='pantry_consumption_misc_delete'),
]