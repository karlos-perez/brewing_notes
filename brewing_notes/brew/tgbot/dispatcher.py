import logging
import telegram
from telegram.ext import (Updater, Dispatcher, Filters,
                          CommandHandler, MessageHandler,
                          InlineQueryHandler, CallbackQueryHandler,
                          ChosenInlineResultHandler,)
from django.conf import settings

# from brewing_notes.celery import app

from .handlers import command_start, management, main_menu, management_site, management_bot,\
                      recipes_list, recipe_one, recipe_list_ingredients, devices_list, device_one,\
                      device_data, command_help, command_menu, command_recipe, command_device,\
                      device_chart
from .manage_data import MANAGE_BUTTON, MAIN_MENU_BUTTON, MANAGE_SITE_BUTTON, MANAGE_BOT_BUTTON,\
                         RECIPES_BUTTON, RECIPE_ONE_BUTTON, RECIPE_LIST_INGREDIENTS, DEVICES_BUTTON,\
                         DEVICE_ONE_BUTTON, DEVICE_DATA_BUTTON, DEVICE_CHART_BUTTON


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    # Start & Auth
    dp.add_handler(CommandHandler("start", command_start))
    # Help
    dp.add_handler(CommandHandler("help", command_help))
    dp.add_handler(CommandHandler("menu", command_menu))
    dp.add_handler(CommandHandler("recipe", command_recipe))
    dp.add_handler(CommandHandler("device", command_device))
    # main menu
    dp.add_handler(CallbackQueryHandler(main_menu, pattern=f"^{MAIN_MENU_BUTTON}$"))
    # management
    dp.add_handler(CallbackQueryHandler(management, pattern=f"^{MANAGE_BUTTON}$"))
    dp.add_handler(CallbackQueryHandler(management_site, pattern=f"^{MANAGE_SITE_BUTTON}$"))
    dp.add_handler(CallbackQueryHandler(management_bot, pattern=f"^{MANAGE_BOT_BUTTON}$"))
    # recipe
    dp.add_handler(CallbackQueryHandler(recipes_list, pattern=f"^{RECIPES_BUTTON}$"))
    dp.add_handler(CallbackQueryHandler(recipe_one, pattern=f"^{RECIPE_ONE_BUTTON}"))
    dp.add_handler(CallbackQueryHandler(recipe_list_ingredients, pattern=f"^{RECIPE_LIST_INGREDIENTS}"))
    # devices
    dp.add_handler(CallbackQueryHandler(devices_list, pattern=f"^{DEVICES_BUTTON}$"))
    dp.add_handler(CallbackQueryHandler(device_one, pattern=f"^{DEVICE_ONE_BUTTON}"))
    dp.add_handler(CallbackQueryHandler(device_data, pattern=f"^{DEVICE_DATA_BUTTON}"))
    dp.add_handler(CallbackQueryHandler(device_chart, pattern=f"^{DEVICE_CHART_BUTTON}"))
    # catalog
    # dp.add_handler(CallbackQueryHandler(catalog_main, pattern=f"^{CATALOG_BUTTON}$"))
    return dp


# @app.task(ignore_result=True)
# @app.task
def process_telegram_event(update_json):
    update = telegram.Update.de_json(update_json, bot)
    dispatcher.process_update(update)


# Global variable - best way I found to init Telegram bot

bot = telegram.Bot(settings.TELEGRAM_TOKEN)
dispatcher = setup_dispatcher(Dispatcher(bot, None, workers=0, use_context=True))
TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
