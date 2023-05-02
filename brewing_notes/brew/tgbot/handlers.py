import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localtime

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ForceReply, ParseMode
from telegram.ext import CallbackContext

from nnmware.core.constants import STATUS_CHOICES
from nnmware.core.exceptions import AccessError

from catalog.constants import TYPE_BEER

from ..constants import ADMIN, STATUS_CONFORMITY, DEVICE_TYPE, DEVICE_BREWPILESS, DEVICE_ISPINDEL
from ..models import UserTelegramProfile, get_site_statistic

from .keyboards import main_menu_keyboard, management_main_menu_keyboard, management_footer_keyboard,\
                       recipes_my_list_keyboard, recipe_keyboard, device_keyboard, devices_list_keyboard
from .static_text import *
from .manage_data import RECIPE_ONE_BUTTON, RECIPE_LIST_INGREDIENTS, DEVICE_ONE_BUTTON, DEVICE_DATA_BUTTON,\
                         DEVICE_CHART_BUTTON
from .utils import get_user, extract_user_data_from_update, get_recipe, get_device, get_device_data,\
                   get_chart_image, auth_users, admin_users


logger = logging.getLogger(__name__)


def login_check(func):
    def wrap(*args, **kwargs):
        user_id = extract_user_data_from_update(args[0])['user_id']
        if user_id in auth_users():
            func(*args, **kwargs)
        else:
            args[1].bot.send_message(text=access_denied,
                                     chat_id=user_id,
                                     parse_mode=ParseMode.HTML)
    return wrap


def admin_check(func):
    def wrap(*args, **kwargs):
        user_id = extract_user_data_from_update(args[0])['user_id']
        if user_id in admin_users():
            func(*args, **kwargs)
        else:
            args[1].bot.send_message(text=access_denied,
                                     chat_id=user_id,
                                     parse_mode=ParseMode.HTML)
    return wrap


def command_start(update, context):
    data = extract_user_data_from_update(update)
    u = get_user(update)
    if data['user_id'] in auth_users() and u is not None:
        result = f'<b> - - - {main_menu_section} - - - </b>'
        keyboard = main_menu_keyboard(u.is_admin)
    else:
        text = update.message.text.split(' ')
        if len(text) > 1:
            token = text[1]
            usr = cache.get(token)
            if usr is not None:
                usr = cache.get(token)
                try:
                    user = get_user_model().objects.get(id=usr)
                    user_profile, created = UserTelegramProfile.objects.get_or_create(user=user)
                    if not created:
                        if user_profile.is_banned:
                            raise AccessError
                        else:
                            user_profile.enabled = True
                            user_profile.is_blocked_bot = False
                            user_profile.is_banned = False
                            user_profile.receive_notification = True
                    user_profile.user = user
                    user_profile.user_tg_id = data['user_id']
                    user_profile.username = data.get('username', '')
                    user_profile.first_name = data.get('first_name', '')
                    user_profile.last_name = data.get('last_name', '')
                    user_profile.language_code = data.get('language_code', '')
                    # user_profile.enabled = True
                    # user_profile.is_blocked_bot = False
                    # user_profile.is_banned = False
                    # user_profile.receive_notification = True
                    user_profile.save()
                    if context is not None and context.args is not None and len(context.args) > 0:
                        payload = context.args[0]
                        if str(payload).strip() != str(data['user_id']).strip():  # you can't invite yourself
                            user_profile.deep_link = payload
                            user_profile.save()
                    # if user.is_admin:
                    #     user_profile.is_admin = True
                    # user_profile.save()
                    auth_users(new_set=True)
                    if user.is_admin:
                        admin_users(new_set=True)
                    cache.delete(token)
                    result = welcome.format(name=user.username)
                    keyboard = main_menu_keyboard(user.is_admin)
                except AccessError:
                    result = access_denied
                    keyboard = None
                except Exception as err:
                    logger.error(f'Error auth TG User.id: {usr} | {err} | {data}')
            else:  # no in cache token
                result = access_denied
                keyboard = None
        else:  # not token and user is not auth
            result = access_denied
            keyboard = None
    update.message.reply_text(text=result,
                              reply_markup=keyboard,
                              parse_mode=ParseMode.HTML)


@login_check
def command_help(update, context):
    text = help_text
    update.message.reply_text(text=text,
                              parse_mode=ParseMode.HTML)


@login_check
def command_menu(update, context):
    text = f'<b> - - - {main_menu_section} - - - </b>'
    keyboard = main_menu_keyboard(get_user(update).is_admin)
    update.message.reply_text(text=text,
                              reply_markup=keyboard,
                              parse_mode=ParseMode.HTML)


@login_check
def command_recipe(update, context):
    user = get_user(update)
    keyboard = recipes_my_list_keyboard(user.all_recipes)
    text = f'<b> - - - {recipe_list} - - - </b>'
    update.message.reply_text(text=text,
                              reply_markup=keyboard,
                              parse_mode=ParseMode.HTML)


@login_check
def command_device(update, context):
    user = get_user(update)
    keyboard = devices_list_keyboard(user.all_device)
    text = f'<b> - - - {device_list} - - - </b>'
    update.message.reply_text(text=text,
                              reply_markup=keyboard,
                              parse_mode=ParseMode.HTML)


@login_check
def main_menu(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    if user_id in admin_users():
        keyboard = main_menu_keyboard(True)
    else:
        keyboard = main_menu_keyboard(False)
    text = f'<b> - - - {main_menu_section} - - - </b>'
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML,)


@admin_check
def management(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    keyboard = management_main_menu_keyboard()
    text = f'<b> - - - {management_section} - - - </b>'
    context.bot.edit_message_text(text=text,
                                  chat_id=user_id,
                                  message_id=update.callback_query.message.message_id,
                                  parse_mode=ParseMode.HTML,
                                  reply_markup=keyboard)


@admin_check
def management_site(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    stat = get_site_statistic()
    text = statistic_site.format(users_all=stat['users_all'],
                                 users_today=len(stat['users_today']),
                                 new_users_today=len(stat['new_users_today']),
                                 recipes_all=stat['recipes_all'],
                                 recipes_pub=stat['recipes_pub'],
                                 recipes_mod=stat['recipes_mod'],
                                 recipes_draft=stat['recipes_draft'],
                                 recipes_today=len(stat['recipes_today']))
    if len(stat['users_today']) > 0:
        users = today_users
        for i in stat['users_today']:
            users += f'{i.username}\n'
        text += users
    if len(stat['new_users_today']) > 0:
        users = new_today_users
        for i in stat['new_users_today']:
            users += f'{i.username} | {i.email}\n'
        text += users
    if len(stat['recipes_today']) > 0:
        recipes = today_recipes
        for i in stat['recipes_today']:
            recipes += f'{i.name} ({i.user.username})\n'
        text += recipes
    keyboard = management_footer_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)


@admin_check
def management_bot(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    text = statistic_bot.format(users_all=len(auth_users()),
                                users_mod=len(admin_users()))
    keyboard = management_footer_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)


@login_check
def recipes_list(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = get_user(update)
    keyboard = recipes_my_list_keyboard(user.all_recipes)
    text = f'<b> - - - {recipe_list} - - - </b>'
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(text=text,
                             chat_id=user_id,
                             parse_mode=ParseMode.HTML,
                             reply_markup=keyboard)


@login_check
def recipe_one(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    recipe_id = update.callback_query.data[len(RECIPE_ONE_BUTTON):]
    recipe = get_recipe(recipe_id.strip())
    user = get_user(update)
    if recipe is not None or recipe.user != user:
        text = recipe_info.format(name=recipe.name,
                                  style=recipe.style,
                                  type=TYPE_BEER[recipe.type][1],
                                  status=STATUS_CHOICES[recipe.status][1],
                                  сonformity=STATUS_CONFORMITY[recipe.сonformity][1],
                                  pbg=recipe.PBG,
                                  og=recipe.OG,
                                  fg=recipe.FG,
                                  abv=recipe.abv,
                                  ibu=recipe.ibu,
                                  srm=recipe.srm,
                                  batch_size=recipe.batch_size,
                                  mash_water=recipe.mash_water,
                                  sparge_water=recipe.sparge_water,
                                  pre_boil_size=recipe.pre_boil_size,
                                  sediment_after_boil=recipe.sediment_after_boil,
                                  starter_volume=recipe.starter_volume,
                                  bottling_size=recipe.bottling_size,
                                  boil_time=recipe.boil_time,
                                  efficiency_mash=recipe.efficiency_mash,
                                  url=recipe.get_full_short_link())
        keyboard = recipe_keyboard(recipe.id)
    else:
        text = recipe_not_found
        keyboard = recipe_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)


@login_check
def recipe_list_ingredients(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    recipe_id = update.callback_query.data[len(RECIPE_LIST_INGREDIENTS):]
    recipe = get_recipe(recipe_id.strip())
    user = get_user(update)
    if recipe is not None and recipe.user == user:
        text = recipe_list_all_ingredients.format(name=recipe.name)
        for n, i in recipe.get_list_ingredients.items():
            ing = f'<b><i>{i["type"]}:</i></b> {i["name"]} <b>{i["amount"]}{i["measure"]}</b>\n'
            text += ing
    else:
        text = recipe_not_found
    keyboard = recipe_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)


@login_check
def devices_list(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    user = get_user(update)
    if user.all_device:
        keyboard = devices_list_keyboard(user.all_device)
        text = f'<b> - - - {device_list} - - - </b>'
    else:
        keyboard = main_menu_keyboard(False)
        text = device_none
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(text=text,
                             chat_id=user_id,
                             parse_mode=ParseMode.HTML,
                             reply_markup=keyboard)


@login_check
def device_one(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    device_id = update.callback_query.data[len(DEVICE_ONE_BUTTON):]
    device = get_device(device_id.strip())
    latest_data = cache.get(device.token)
    user = get_user(update)
    if device is not None and device.active and device.user == user:
        text = device_info.format(name=device.name,
                                  type=DEVICE_TYPE[device.type][1],
                                  token=device.token,
                                  count=device.devicedatalog_set.count(),)
        if latest_data is None:
            data = device_not_last_data
        else:
            if device.type == DEVICE_BREWPILESS:
                data = device_bpl_last_data.format(beer_temp=latest_data['beer_temp'],
                                                   fridge_temp=latest_data['fridge_temp'],
                                                   root_temp=latest_data['root_temp'],
                                                   aux_temp=latest_data['aux_temp'],
                                                   gravity=latest_data['gravity'],
                                                   tilt=latest_data['tilt'],
                                                   volt=latest_data['volt'],
                                                   pressure=latest_data['pressure'],
                                                   time=localtime(latest_data['time']).strftime("%d.%m.%Y %H:%M"))
            elif device.type == DEVICE_ISPINDEL:
                data = device_isp_last_data.format(aux_temp=latest_data['aux_temp'],
                                                   gravity=latest_data['gravity'],
                                                   tilt=latest_data['tilt'],
                                                   volt=latest_data['volt'],
                                                   rssi=latest_data['rssi'],
                                                   time=localtime(latest_data['time']).strftime("%d.%m.%Y %H:%M"))
        text += f'{data}'
        keyboard = device_keyboard(device.id)
    else:
        text = device_not_found
        keyboard = device_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)


@login_check
def device_data(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    device_id = update.callback_query.data[len(DEVICE_DATA_BUTTON):]
    device = get_device(device_id.strip())
    data = get_device_data(device)
    text = device_data_10
    user = get_user(update)
    if device is not None and device.active and device.user == user:
        if not data:
            text += device_not_data
        else:
            for i in data:
                inf = f'{localtime(i.created_date).strftime("%H:%M")} '\
                      f'{i.beer_temp:8.1f}\N{DEGREE SIGN}C '\
                      f'{i.aux_temp:8.1f}\N{DEGREE SIGN}C '\
                      f'{i.gravity:10.3f}\n'
                text += inf
        keyboard = device_keyboard(device.id)
    else:
        text = device_not_found
        keyboard = device_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    context.bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)


@login_check
def device_chart(update, context):
    user_id = extract_user_data_from_update(update)['user_id']
    device_id = update.callback_query.data[len(DEVICE_CHART_BUTTON):]
    device = get_device(device_id.strip())
    data = get_chart_image(device)
    text = device_not_data
    user = get_user(update)
    if device is not None and device.active and device.user == user:
        keyboard = device_keyboard(device.id)
    else:
        text = device_not_found
        keyboard = device_keyboard()
    context.bot.delete_message(chat_id=user_id,
                               message_id=update.callback_query.message.message_id)
    if data is not None:
        context.bot.send_photo(chat_id=user_id,
                               photo=data)
    else:
        context.bot.send_message(chat_id=user_id,
                                 text=text,
                                 parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=user_id,
                             text=next_action,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)

