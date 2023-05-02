from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from nnmware.core.constants import STATUS_PUBLISHED, STATUS_MODERATION, STATUS_DRAFT

from ..constants import DEVICE_TYPE

from .manage_data import *
from .static_text import *


status_recipe = {STATUS_PUBLISHED: '📖',
                 STATUS_MODERATION: '📨',
                 STATUS_DRAFT: '📋'}
status_device = {True: '✅',
                 False: '❎'}

main_menu_buttons = InlineKeyboardButton(back_main_menu, callback_data=f'{MAIN_MENU_BUTTON}')

management_menu_button = InlineKeyboardButton(management_section, callback_data=f'{MANAGE_BUTTON}')


def main_menu_keyboard(admin: bool) -> object:
    buttons = [[InlineKeyboardButton(devices_section, callback_data=f'{DEVICES_BUTTON}'),
                InlineKeyboardButton(recipes_section, callback_data=f'{RECIPES_BUTTON}')]]
    if admin:
        buttons.insert(0, [management_menu_button,])
    return InlineKeyboardMarkup(buttons)


def management_main_menu_keyboard() -> object:
    buttons = [[InlineKeyboardButton(management_site, callback_data=f'{MANAGE_SITE_BUTTON}'),
                InlineKeyboardButton(management_bot, callback_data=f'{MANAGE_BOT_BUTTON}')],
               [main_menu_buttons,]]
    return InlineKeyboardMarkup(buttons)


def management_footer_keyboard() -> object:
    buttons = [[InlineKeyboardButton(management_back_section, callback_data=f'{MANAGE_BUTTON}'),
                InlineKeyboardButton(back_main_menu, callback_data=f'{MAIN_MENU_BUTTON}')]]
    return InlineKeyboardMarkup(buttons)


def recipes_my_list_keyboard(recipes: list) -> object:
    buttons = list()
    for r in recipes:
        button = [InlineKeyboardButton(f'{status_recipe[r.status]} {r.name}', callback_data=f'{RECIPE_ONE_BUTTON} {r.id}')]
        buttons.append(button)
    buttons.append([main_menu_buttons,])
    return InlineKeyboardMarkup(buttons)


def recipe_keyboard(recipe_id=0) -> object:
    buttons = [[InlineKeyboardButton(recipes_back_section, callback_data=f'{RECIPES_BUTTON}'),
                InlineKeyboardButton(back_main_menu, callback_data=f'{MAIN_MENU_BUTTON}')]]
    if recipe_id:
        recipe_button = [InlineKeyboardButton(recipe_ingredients, callback_data=f'{RECIPE_LIST_INGREDIENTS} {recipe_id}')]

        buttons.insert(0, recipe_button)
    return InlineKeyboardMarkup(buttons)


def devices_list_keyboard(devices: list) -> object:
    buttons = list()
    for d in devices:
        button = [InlineKeyboardButton(f'{status_device[d.active]} {d.name} ({DEVICE_TYPE[d.type][1]})', callback_data=f'{DEVICE_ONE_BUTTON} {d.id}')]
        buttons.append(button)
    buttons.append([main_menu_buttons,])
    return InlineKeyboardMarkup(buttons)


def device_keyboard(device_id=0) -> object:
    buttons = [[InlineKeyboardButton(devices_back_section, callback_data=f'{DEVICES_BUTTON}'),
                InlineKeyboardButton(back_main_menu, callback_data=f'{MAIN_MENU_BUTTON}')]]
    if device_id:
        recipe_button = [[InlineKeyboardButton(device_update_data, callback_data=f'{DEVICE_ONE_BUTTON} {device_id}')],
                         [InlineKeyboardButton(device_data, callback_data=f'{DEVICE_DATA_BUTTON} {device_id}'),
                          InlineKeyboardButton(device_chart, callback_data=f'{DEVICE_CHART_BUTTON} {device_id}')]]
        buttons = recipe_button + buttons
    return InlineKeyboardMarkup(buttons)


