import logging
import io

from PIL import Image
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from ..constants import ADMIN
from ..models import UserTelegramProfile, Recipe, ConnectedDevice


logger = logging.getLogger(__name__)


def users_mailing_list(new_set=False):
    if new_set:
        cache.delete('TG_USERS_MAILING_LIST')
    users_list = cache.get('TG_USERS_MAILING_LIST')
    if users_list is None:
        users_list = list(UserTelegramProfile.objects.filter(enabled=True,
                                                             is_blocked_bot=False,
                                                             is_banned=False,
                                                             receive_notification=True).values_list('user_tg_id', flat=True))
        cache.add('TG_USERS_MAILING_LIST', users_list, settings.CACHE_TTL_LOG)
    return users_list


def auth_users(new_set=False):
    if new_set:
        cache.delete('TG_AUTH_USERS')
    users_list = cache.get('TG_AUTH_USERS')
    if users_list is None:
        users_list = list(UserTelegramProfile.objects.filter(enabled=True,
                                                             is_banned=False,
                                                             is_blocked_bot=False).values_list('user_tg_id', flat=True))
        cache.add('TG_AUTH_USERS', users_list, settings.CACHE_TTL_LOG)
    return users_list


def admin_users(new_set=False):
    if new_set:
        cache.delete('TG_ADMIN_USERS')
    admin_list = cache.get('TG_ADMIN_USERS')
    if admin_list is None:
        admin_list = list(UserTelegramProfile.objects.filter(enabled=True,
                                                             is_banned=False,
                                                             is_blocked_bot=False,
                                                             user__status=ADMIN).values_list('user_tg_id', flat=True))
        cache.add('TG_ADMIN_USERS', admin_list, settings.CACHE_TTL_LOG)
    return admin_list


def extract_user_data_from_update(update):
    """ python-telegram-bot's Update instance --> User info """
    if update.message is not None:
        user = update.message.from_user.to_dict()
    elif update.inline_query is not None:
        user = update.inline_query.from_user.to_dict()
    elif update.chosen_inline_result is not None:
        user = update.chosen_inline_result.from_user.to_dict()
    elif update.callback_query is not None and update.callback_query.from_user is not None:
        user = update.callback_query.from_user.to_dict()
    elif update.callback_query is not None and update.callback_query.message is not None:
        user = update.callback_query.message.chat.to_dict()
    else:
        raise Exception(f"Can't extract user data from update: {update}")
    return dict(
        user_id=user['id'],
        is_blocked_bot=False,
        **{
            k: user[k]
            for k in ['username', 'first_name', 'last_name', 'language_code']
            if k in user and user[k] is not None
        },
    )


def get_user(update):
    try:
        data = extract_user_data_from_update(update)
        profile = UserTelegramProfile.objects.get(user_tg_id=data['user_id'])
        return profile.user
    except ObjectDoesNotExist as err:
        return None
    except Exception as err:
        logger.error(f'Error get User: user_id={data["user_id"]}: {err}')
        return None


def get_recipe(recipe_id) -> object:
    try:
        recipe = Recipe.objects.get(id=int(recipe_id))
    except Exception as err:
        logger.error(f'Error get Recipe: recipe_id={recipe_id}: {err}')
        recipe = None
    return recipe


def get_device(device_id: str) -> object:
    try:
        device = ConnectedDevice.objects.get(id=int(device_id))
    except Exception as err:
        logger.error(f'Error get Recipe: recipe_id={device_id}: {err}')
        device = None
    return device


def get_device_data(device: object) -> list:
    try:
        data = device.devicedatalog_set.all().order_by('-created_date')[:10]
    except Exception as err:
        logger.error(f'Error get Device data: device_id={device.id} ({device.name}): {err}')
        data = list()
    return data


def add_watermark_on_chart(ax, dpi):
    """
    Add watermark on plot (for telegram bot)
    """
    from matplotlib.offsetbox import OffsetImage, AnchoredOffsetbox

    file_watermark = settings.WATERMARK_FOR_CHART

    img = Image.open(file_watermark)
    width, height = ax.figure.get_size_inches() * dpi
    wm_width = int(width / 2)  # make the watermark 1/2 of the figure size
    scaling = (wm_width / float(img.size[0]))
    wm_height = int(float(img.size[1]) * float(scaling))
    img = img.resize((wm_width, wm_height), Image.ANTIALIAS)

    imagebox = OffsetImage(img, zoom=1, alpha=0.3)
    imagebox.image.axes = ax

    ao = AnchoredOffsetbox(3, pad=0.01, borderpad=0, child=imagebox)
    ao.patch.set_alpha(0)
    ax.add_artist(ao)


def get_chart_image(device: object) -> Image:

    import matplotlib.pyplot as plt
    from matplotlib import dates

    chart = cache.get(f'CHART_IMAGE_{device.token}')
    if chart is not None:
        return chart
    try:
        time_threshold = timezone.now() - timedelta(days=settings.CHART_LIMIT_DAYS)
        data = device.devicedatalog_set.filter(created_date__gt=time_threshold)
        if not data:
            return None

        x = [timezone.localtime(i) for i in data.values_list('created_date', flat=True)]
        y1 = [float(i) for i in data.values_list('beer_temp', flat=True)]
        y2 = [float(i) for i in data.values_list('aux_temp', flat=True)]
        y3 = [float(i) for i in data.values_list('gravity', flat=True)]

        fig, ax_t = plt.subplots(1)
        fmt = dates.DateFormatter('%H:%M')

        y1_lim_min = min(min(y1), min(y2)) - 1
        y1_lim_max = max(max(y1), max(y2)) + 2
        y3_lim_min = min(y3) - 0.05
        y3_lim_max = max(y3) + 0.05

        ax_g = ax_t.twinx()
        ax_g.set_ylim([y3_lim_min, y3_lim_max])
        ax_t.set_ylim([y1_lim_min, y1_lim_max])

        ax_t.plot(x, y1, color='blue', label="Пиво")
        ax_t.plot(x, y2, color='red', label="Устройство")
        ax_g.plot(x, y3, color='green', label="Плотность")

        add_watermark_on_chart(ax_t, fig.dpi)

        ax_t.set_ylabel('Температура')
        ax_g.set_ylabel('Плотность')
        ax_t.xaxis.set_major_formatter(fmt)

        ax_t.legend(loc='right', bbox_to_anchor=(0.5, -0.10), shadow=False, ncol=2, frameon=False)
        ax_g.legend(loc='center', bbox_to_anchor=(0.7, -0.10), shadow=False, frameon=False)

        ax_t.grid(axis='both')
        plt.title(f'{device.name} с {x[0].strftime("%H:%M %d.%m.%Y")} по {x[-1].strftime("%H:%M %d.%m.%Y")}')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        im = buf.getvalue()

        cache.set(f'CHART_IMAGE_{device.token}', im, settings.CHART_CACHE_MINUTES)
    except Exception as err:
        logger.error(f'Error get Chart Image: {err}, device: {device}')
        im = None
    return im



