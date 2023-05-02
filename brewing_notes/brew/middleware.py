import json

from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

from nnmware.core.utils import setting
from nnmware.core.http import get_session_from_request
from nnmware.core.models import VisitorHit

from logdata.models import DeviceRawData

from .models import VisitorData

UNTRACKED_USER_AGENT = [
    "Teoma", "alexa", "froogle", "Gigabot", "inktomi", "looksmart", "URL_Spider_SQL", "Firefly",
    "NationalDirectory", "Ask Jeeves", "TECNOSEEK", "InfoSeek", "WebFindBot", "girafabot", "crawler",
    "www.galaxy.com", "Googlebot", "Googlebot/2.1", "Google", "Webmaster", "Scooter", "James Bond",
    "Slurp", "msnbot", "appie", "FAST", "WebBug", "Spade", "ZyBorg", "rabaz", "Baiduspider",
    "Feedfetcher-Google", "TechnoratiSnoop", "Rankivabot", "Mediapartners-Google", "Sogou web spider",
    "WebAlta Crawler", "MJ12bot", "Yandex/", "YandexBot", "YaDirectBot", "StackRambler", "DotBot", "dotbot",
    "AhrefsBot", "Mail.RU_Bot", "YandexDirect", "Twitterbot", "PaperLiBot", "bingbot", "Ezooms", 'SiteExplorer',
    "PetalBot", "YandexTurbo"
]

DEVICE_USER_AGENT = 'ESP8266'

class VisitorHitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.is_ajax():
            return
        if request.path.startswith(setting('ADMIN_SYSTEM_PREFIX', '/admin/')):
            return
            # see if the user agent is not supposed to be tracked
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        if DEVICE_USER_AGENT in user_agent:
            d = DeviceRawData()
            d.token = request.GET.get('token', '-')
            d.user_agent = user_agent
            d.ip = request.META.get('REMOTE_ADDR', '')
            d.referer = request.META.get('HTTP_REFERER', '')
            d.hostname = request.META.get('REMOTE_HOST', '')[:100]
            d.url = request.get_full_path()
            d.date = now()
            d.body = request.body.decode('UTF-8')
            d.save()
            return
        for ua in UNTRACKED_USER_AGENT:
            # if the keyword is found in the user agent, stop tracking
            if user_agent.find(ua) != -1:
                return
        v = VisitorHit()
        if request.user.is_authenticated:
            v.user = request.user
        v.user_agent = user_agent
        v.ip = request.META.get('REMOTE_ADDR', '')
        v.session_key = get_session_from_request(request)
        v.secure = request.is_secure()
        v.referer = request.META.get('HTTP_REFERER', '')
        v.hostname = request.META.get('REMOTE_HOST', '')[:100]
        v.url = request.get_full_path()
        v.date = now()
        v.save()
        if request.user.is_authenticated:
            VisitorData.objects.get_or_create(user=request.user,
                                              ip=request.META.get('REMOTE_ADDR', ''),
                                              user_agent=user_agent)
            # try:
            #     vd = VisitorData()
            #     vd.user = request.user
            #     vd.ip = request.META.get('REMOTE_ADDR', '')
            #     v.user_agent = user_agent
            #     vd.date = now()
            #     vd.save()
            # except Exception as err:
            #     pass
