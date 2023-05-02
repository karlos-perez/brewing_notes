from django.conf import settings

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from nnmware.core.ajax import avatar_set, avatar_delete, like, delete_message

from .ajax import *
from .decorators import check_recaptcha
from .views import *


urlpatterns = [
    path('', MainPageView.as_view(), name='main'),
    path('login/', BrewLoginView.as_view(), name="login"),
    path('registration/', check_recaptcha(RegisterUserView.as_view()), name='registration'),
    path('confirmation/<str:confirm_key>', ConfirmationEmailView.as_view(), name='confirmation'),
    path('confirmation/resend/', ConfirmationResendView.as_view(), name='confirmation_resend'),
    path('restore/', check_recaptcha(RestorePasswordView.as_view()), name='restore'),
    path('restore/<str:activation_key>', BrewUserRecoverView.as_view(), name='recover_user'),
    path('logout/', Logout.as_view(), name='logout'),
    path('feedback/', check_recaptcha(FeedbackView.as_view()), name='feedback'),
    path('about/', AboutView.as_view(), name='about_us'),
    path('about/regulations', RegulationsView.as_view(), name='regulations'),

    path('l<str:uid>', RecipeShareLiteView.as_view(), name='recipes_print_lite'),
    path('f<str:key>', RecipeShareFullView.as_view(), name='recipe_temp_full'),
    path('recipes/', RecipesListView.as_view(), name='recipes_list'),
    path('recipes/public', RecipesPublicListView.as_view(), name='recipes_public_list'),
    path('recipes/card/<str:uid>', RecipePublicView.as_view(), name='recipe_card'),
    path('recipes/<uuid:slug>/', RecipeView.as_view(), name='recipe_detail'),
    path('recipes/<uuid:slug>/pdf', RecipePDFView.as_view(), name='recipes_pdf'),
    path('recipes/<uuid:slug>/brewcard', RecipeBrewCardPDFView.as_view(), name='recipes_brewcard'),
    path('recipes/<uuid:slug>/label', RecipeLabelPDFView.as_view(), name='recipe_label'),
    path('recipes/<uuid:slug>/bxml', RecipeBXMLView.as_view(), name='recipes_bxml'),
    path('recipes/<uuid:slug>/copy', RecipeCopyView.as_view(), name='recipes_copy'),
    path('recipes/<uuid:slug>/publishing/', RecipePublishingView.as_view(), name='recipe_publishing'),
    path('recipes/<uuid:slug>/delete/', RecipeDeleteView.as_view(), name='recipe_delete'),
    path('recipes/<uuid:slug>/analysis/', RecipeAnalysisView.as_view(), name='recipe_analysis'),
    path('recipes/<uuid:slug>/ingredients/', RecipeIngredientsListView.as_view(), name='recipes_ingredients'),
    path('recipes/add/', RecipeAddFullView.as_view(), name='recipe_add'),
    path('recipes/edit/<uuid:slug>', RecipeEditFullView.as_view(), name='recipe_edit'),
    path('recipes/<int:object_id>/chart/save/', RecipeChartSaveView.as_view(), name='recipe_chart_save'),

    path('user/recipes/<str:username>', UserRecipesListView.as_view(), name='user_recipes'),
    path('user/recipes/<str:username>/favorites', UserFavoritesListView.as_view(), name='user_favorites'),
    path('user/messages/new', UserMessagesNewView.as_view(), name='user_messages_new'),
    path('user/messages/inbox', UserMessagesInboxView.as_view(), name='user_messages_inbox'),
    path('user/messages/sendbox', UserMessagesSendboxView.as_view(), name='user_messages_sendbox'),
    path('user/profile/<str:username>', UserDetailView.as_view(), name='user_detail'),
    path('user/device/add/', UserDeviceAddView.as_view(), name='user_device_add'),
    path('user/module/add/', UserModuleAddView.as_view(), name='user_module_add'),
    path('user/device/setting/save/', UserDeviceSettingView.as_view(), name='user_device_setting'),
    path('user/water-profile/add/', UserWaterAddView.as_view(), name='user_water_add'),
    path('user/trial/refusal/', UserTrialRefusalView.as_view(), name='user_refusal_trial'),
    path('user/trial/activate/', UserTrialActivateView.as_view(), name='user_activate_trial'),
    path('user/telegram/<str:username>/delete/', UserTelegramDeleteView.as_view(), name='user_telegram_delete'),
    path('user/<str:username>/delete/', UserDeleteView.as_view(), name='user_delete'),

    path('management/dashboard/', AdminMainView.as_view(), name='admn_main'),
    path('management/moderations/', AdminModerationsView.as_view(), name='admn_moderations'),
    path('management/recipes/', AdminRecipesListView.as_view(), name='admn_recipes_list'),
    path('management/recipe/<slug:slug>', AdminRecipeView.as_view(), name='admn_recipe_one'),
    path('management/recipe/<slug:slug>/refusion/', AdminRecipeRefusionView.as_view(), name='admn_recipe_refusion'),
    path('management/users/', AdminUsersListView.as_view(), name='admn_users_list'),
    path('management/user/<str:username>', AdminUserView.as_view(), name='admn_user_one'),
    path('management/user/<str:username>/ban/', AdminUserBanView.as_view(), name='admn_user_ban'),
    path('management/devices/', AdminDevicesListView.as_view(), name='admn_devices_list'),
    path('management/devices/raw/', AdminDevicesRawDataView.as_view(), name='admn_devices_raw_data'),
    path('management/actions/', AdminActionsListView.as_view(), name='admn_actions_list'),
    path('management/souls/', AdminSoulsListView.as_view(), name='admn_souls_list'),

    path('computing/calcs/', ComputingBrewView.as_view(), name='computing_main'),
    path('computing/recipe/', ComputingRecipeView.as_view(), name='create_recipe'),
    path('computing/recipe/save/', ComputingRecipeSaveView.as_view(), name='save_recipe'),
    path('computing/other/', ComputingOtherView.as_view(), name='computing_other'),
    path('computing/water/', ComputingWaterView.as_view(), name='computing_water'),
    path('computing/water/save/', ComputingWaterSaveView.as_view(), name='computing_water_save'),

    path('telemetry/bnc-modules/', ModulesListView.as_view(), name='modules_list'),
    path('telemetry/equipment/', EquipmentsListView.as_view(), name='equipments_list'),
    path('telemetry/equipment/help/', EquipmentsHelpView.as_view(), name='equipments_help'),
    path('telemetry/equipment/add/', EquipmentAddView.as_view(), name='equipment_add'),
    path('telemetry/equipment/fermenter/<int:object_id>', EquipmentFermenterView.as_view(), name='equipment_fermenter'),
    path('telemetry/equipment/kettle/<int:object_id>', EquipmentKettleView.as_view(), name='equipment_kettle'),
    path('telemetry/equipment/delete/<int:object_id>', EquipmentDeleteView.as_view(), name='equipment_delete'),
    path('telemetry/device/<str:token>/', DeviceInfoView.as_view(), name='device_info'),
    path('telemetry/cleardata/<str:token>/', DeviceClearDataView.as_view(), name='device_clear'),

    path(f'tghook/{settings.TELEGRAM_TOKEN}/', csrf_exempt(TelegramBotWebhookView.as_view())),
    # path(f'tghook/', csrf_exempt(TelegramBotWebhookView.as_view())),

    path('api/v1/avatar/set/', avatar_set, name='avatar_set'),
    path('api/v1/avatar/delete/', avatar_delete, name='avatar_delete'),
    path('api/v1/logo/<str:content_type>/<str:object_id>/set/', user_image_attach, name='pic_ajax'),
    path('api/v1/logo/delete/', logo_delete, name='logo_delete'),
    path('api/v1/cover/set/', cover_set, name='cover_set'),
    path('api/v1/cover/delete/', cover_delete, name='cover_delete'),
    path('api/v1/settings/', user_settings, name='user_settings'),
    path('api/v1/favorite/', favorite_recipe, name='favorite_recipe'),
    path('api/v1/like/<int:content_type>/<int:object_id>', like, name='like'),
    path('api/v1/read/message/<int:object_id>', read_message, name='read_message'),
    path('api/v1/push/message/<int:pk>', push_message, name='push_message'),
    path('api/v1/delete/message/<int:object_id>', delete_message, name='delete_message'),
    path('api/v1/recipe/create/', computing_recipe, name='computing_recipe'),
    path('api/v1/recipe/<uuid:slug>/chart/', get_recipe_chart, name='get_recipe_chart'),
    path('api/v1/recipe/<uuid:slug>/visibility/', set_recipe_visibility, name='set_recipe_visibility'),
    path('api/v1/recipe/get-url/', get_temp_url_recipe, name='get_temp_url_recipe'),
    path('api/v1/recipe/delete-url/', delete_temp_url_recipe, name='delete_temp_url_recipe'),

    path('api/v1/device/status/<int:object_id>', device_status, name='device_status'),
    path('api/v1/device/delete/<int:object_id>', device_delete, name='device_delete'),
    path('api/v1/module/delete/<int:object_id>', module_delete, name='module_delete'),
    path('api/v1/module/full/reset', module_full_reset, name='module_full_reset'),
    path('api/v1/equipment/save/<int:object_id>', equipment_save, name='equipment_save'),
    path('api/v1/equipment/change/status/<int:object_id>', equipment_status, name='equipment_status'),
    path('api/v1/equipment/reset/data/<int:object_id>', equipment_reset, name='equipment_reset'),

    path('api/v1/user/water-profile/delete/<int:object_id>', user_water_delete, name='user_water_delete'),

    path('api/v1/bot/add/', get_link_login_bot, name='get_link_login_bot'),
    path('api/v1/bot/receive/notif/', tg_receive_notif, name='tg_receive_notif'),
]


