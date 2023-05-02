import logging
import telegram
import time

# from celery.utils.log import get_task_logger
from telegram import ParseMode, MessageEntity

from django.conf import settings

# from brewing_notes.celery import app

from ..models import UserTelegramProfile
from .utils import admin_users, users_mailing_list


logger = logging.getLogger(__name__)
# logger_c = get_task_logger(__name__)


def send_tg_users(text):
    users_list = users_mailing_list()
    if users_list:
        if settings.DEBUG:
            broadcast_message(users_list, text, parse_mode=ParseMode.HTML)
        else:
            broadcast_message(users_list, text, parse_mode=ParseMode.HTML)
            # broadcast_message.delay(users_list, text, parse_mode=ParseMode.HTML)


def send_tg_admins(text):
    admins_list = admin_users()
    if admins_list:
        if settings.DEBUG:
            broadcast_message(admins_list, text, parse_mode=ParseMode.HTML)
        else:
            broadcast_message(admins_list, text, parse_mode=ParseMode.HTML)
            # broadcast_message.delay(admins_list, text, parse_mode=ParseMode.HTML)


def send_tg_user(user, text, parse_mode=ParseMode.HTML):
    if hasattr(user, 'usertelegramprofile'):
        users_list = users_mailing_list()
        user_id = user.usertelegramprofile.user_tg_id
        if user_id in users_list:
            send_message(user_id, text, parse_mode=parse_mode)


# @app.task
def broadcast_message(user_ids, message, entities=None, sleep_between=0.4, parse_mode=None):
    """ It's used to broadcast message to big amount of users """
    # logger_c.info(f"Going to send message: '{message}' to {len(user_ids)} users")

    for user_id in user_ids:
        try:
            send_message(user_id=user_id, text=message,  entities=entities, parse_mode=parse_mode)
            # logger_c.info(f"Broadcast message was sent to {user_id}")
        except Exception as err:
            logger.error(f"Failed to send message to {user_id}, reason: {err}")
            # logger_c.error(f"Failed to send message to {user_id}, reason: {err}")
        time.sleep(max(sleep_between, 0.1))
    # logger_c.info("Broadcast finished!")


def send_message(user_id, text, parse_mode=None, reply_markup=None, reply_to_message_id=None,
                 disable_web_page_preview=None, entities=None, tg_token=settings.TELEGRAM_TOKEN):
    bot = telegram.Bot(tg_token)
    try:
        if entities:
            entities = [MessageEntity(type=entity['type'],
                                      offset=entity['offset'],
                                      length=entity['length'])
                        for entity in entities]
        m = bot.send_message(chat_id=user_id,
                             text=text,
                             parse_mode=parse_mode,
                             reply_markup=reply_markup,
                             reply_to_message_id=reply_to_message_id,
                             disable_web_page_preview=disable_web_page_preview,
                             entities=entities)
    except telegram.error.Unauthorized:
        logger.error(f"Can't send message to {user_id}. Reason: Bot was stopped.")
        UserTelegramProfile.objects.filter(user_tg_id=user_id).update(is_blocked_bot=True)
        success = False
    except Exception as e:
        logger.error(f"Can't send message to {user_id}. Reason: {e}")
        success = False
    else:
        success = True
        UserTelegramProfile.objects.filter(user_tg_id=user_id).update(is_blocked_bot=False)
    return success

