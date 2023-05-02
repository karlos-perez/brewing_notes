import json
import logging
import os
import secrets
import shutil
from PIL import Image
from hashlib import md5
from io import FileIO, BufferedWriter

from django.conf import settings
from django.contrib.auth import logout, authenticate, login, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files import File
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from nnmware.core.abstract import Pic
from nnmware.core.ajax import ajax_answer_lazy
from nnmware.core.constants import ACTION_DELETED
from nnmware.core.exceptions import AccessError
from nnmware.core.imgutil import remove_thumbnails, remove_file
from nnmware.core.models import Message
from nnmware.core.signals import action
from nnmware.core.utils import setting, get_date_directory
from .constants import MODE_MATCHING, MODULE_OM_NONE

from .models import Recipe, ConnectedDevice, UserTelegramProfile, WaterUserProfile, Modules, EquipmentModules
from .tgbot.static_text import send_message_user
from .tgbot.dispatch import send_tg_user


logger = logging.getLogger(__name__)


class AjaxUploader(object):
    BUFFER_SIZE = 10485760  # 10MB

    def __init__(self, filetype='file', upload_dir='buffer_files', size_limit=10485760):
        self._upload_dir = os.path.join(upload_dir, get_date_directory())
        self._filetype = filetype
        if filetype == 'image':
            self.upload_formats = setting('IMAGE_UPLOAD_FORMAT', ['jpeg', 'jpg'])
        else:
            self._save_format = None
        self._size_limit = size_limit

    def max_size(self):
        """
        Checking file max size
        """
        if int(self._destination.tell()) > self._size_limit:
            self._destination.close()
            os.remove(self._filepath)
            return True

    def setup(self, filename):
        ext = os.path.splitext(filename)[1]
        self._filename = md5(filename.encode('utf8')).hexdigest() + ext
        self._path = os.path.join(self._upload_dir, self._filename)
        self._realpath = os.path.realpath(os.path.dirname(self._path))
        try:
            os.makedirs(self._realpath)
        except:
            pass
        self._filepath = os.path.join(self._realpath, self._filename)
        self._destination = BufferedWriter(FileIO(self._filepath, 'w'))

    def handle_upload(self, request):
        is_raw = True
        if request.FILES:
            is_raw = False
            if len(request.FILES) == 1:
                _var, upload = request.FILES.popitem()
            else:
                return dict(success=False, error=_('Bad upload'))
            upload = upload[0]
            filename = upload.name
        else:
            # the file is stored raw in the request
            upload = request
            # get file size
            try:
                filename = request.GET['qqfile']
            except KeyError as aerr:
                return dict(success=False, error=_("Can't read file name"))
        self.setup(filename)
        try:
            if is_raw:
                # File was uploaded via ajax, and is streaming in.
                chunk = upload.read(self.BUFFER_SIZE)
                while len(chunk) > 0:
                    self._destination.write(chunk)
                    if self.max_size():
                        raise IOError
                    chunk = upload.read(self.BUFFER_SIZE)
            else:
                # File was uploaded via a POST, and is here.
                for chunk in upload.chunks():
                    self._destination.write(chunk)
                    if self.max_size():
                        raise IOError
        except:
            # things went badly.
            return dict(success=False, error=_('Upload error'))
        self._destination.close()
        if self._filetype == 'image':
            try:
                i = Image.open(self._filepath)
            except Exception as err:
                os.remove(self._filepath)
                return dict(success=False, error=_('File is not image format'))
            f_name, f_ext = os.path.splitext(self._filename)
            f_without_ext = os.path.splitext(self._filepath)[0]
            f_format = f_ext.split('.')[-1]
            if f_format.lower() in self.upload_formats:
                self._save_format = f_format.lower()
            else:
                return dict(success=False, error=_(f'Not supported image file format {self._filename} - {f_ext.lower()}'))
            new_path = ".".join([f_without_ext, self._save_format])
            if setting('IMAGE_STORE_ORIGINAL', False):
                # TODO need change the extension
                orig_path = ".".join([f_without_ext + '_orig', self._save_format])
                shutil.copy2(self._filepath, orig_path)
            i.thumbnail((1200, 1200), Image.ANTIALIAS)
            try:
                if self._filepath != new_path:
                    os.remove(self._filepath)
                    self._filepath = new_path
                else:
                    pass
                i.save(self._filepath)
            except Exception as err:
                try:
                    os.remove(self._filepath)
                    os.remove(new_path)
                except:
                    pass
                return dict(success=False, error=_(f'Error saving image'))
            self._filename = ".".join([f_name, self._save_format])
            filepath = '{0}/{1}'.format(self._upload_dir, self._filename)
        return dict(success=True, filepath=filepath, path=self._upload_dir,
                    old_filename=filename, filename=self._filename)


def valid_pass(password, user):
    result = None
    try:
        validate_password(password, user=user)
    except Exception as err:
        result = list(err)
    return result


def user_settings(request):
    try:
        error = None
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)
        user = request.user
        if email is not None:
            try:
                validate_email(email)
                user.email = email
                user.save()
            except:
                pass
        if password is not None:
            error = valid_pass(password, user)
            if error:
                raise AccessError
            user.set_password(password)
            user.save()
            username = request.user.username
            logout(request)
            user = authenticate(username=username, password=password)
            login(request, user)
        payload = {'success': True,
                   'location': user.get_absolute_url(),
                   'result': _(f'Settings have been saved')}
    except Exception as err:
        logger.error(f'Settings saved error: {err}')
        if error:
            payload = {'success': False, 'error': error}
        else:
            payload = {'success': False, 'error': err}
    return ajax_answer_lazy(payload)


def avatar_set(request):
    u = request.user
    upload = os.path.join(settings.MEDIA_ROOT, 'img')
    uploader = AjaxUploader(filetype='image', upload_dir=upload, size_limit=4096000)
    result = uploader.handle_upload(request)
    if result['success']:
        try:
            remove_thumbnails(u.img.path)
            remove_file(u.img.path)
        except:
            pass
        imgfile = result['filepath']
        u.img.save(result['filename'], File(open(imgfile, 'rb')))
        u.save()
        os.remove(imgfile)
        try:
            addons = dict(html=render_to_string('user/avatar.html', {'object': u}))
        except:
            addons = dict()
        result.update(addons)
    return ajax_answer_lazy(result)


def avatar_delete(request):
    try:
        u = request.user
        remove_thumbnails(u.img.path)
        remove_file(u.img.path)
        u.img = ''
        u.save()
        payload = dict(success=True)
        try:
            addons = dict(html=render_to_string('user/avatar.html', {'object': u}))
        except:
            addons = dict()
        payload.update(addons)
    except:
        payload = dict(success=False)
    return ajax_answer_lazy(payload)


def cover_set(request):
    r = get_object_or_404(Recipe, pk=request.POST.get('pk'))
    upload = os.path.join(settings.MEDIA_ROOT, 'img')
    uploader = AjaxUploader(filetype='image', upload_dir=upload, size_limit=4096000)
    result = uploader.handle_upload(request)
    if result['success']:
        try:
            remove_thumbnails(r.img.path)
            remove_file(r.img.path)
        except Exception as err:
            pass
        imgfile = result['filepath']
        r.img.save(result['filename'], File(open(imgfile, 'rb')))
        r.save()
        os.remove(imgfile)
        try:
            addons = dict(html=render_to_string('recipe/cover.html', {'object': r}))
        except Exception as err:
            addons = dict()
        result.update(addons)
    return ajax_answer_lazy(result)


def cover_delete(request):
    try:
        r = get_object_or_404(Recipe, pk=request.POST.get('pk'))
        remove_thumbnails(r.img.path)
        remove_file(r.img.path)
        r.img = ''
        r.save()
        payload = dict(success=True)
        try:
            addons = dict(html=render_to_string('recipe/cover.html', {'object': r}))
        except Exception as err:
            addons = dict()
        payload.update(addons)
    except Exception as err:
        payload = {'success': False}
    return ajax_answer_lazy(payload)


def favorite_recipe(request):
    pk = request.POST.get('pk')
    try:
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe.favorites.filter(id=request.user.id).exists():
            recipe.favorites.remove(request.user)
            is_favorite = False
        else:
            recipe.favorites.add(request.user)
            is_favorite = True
        payload = {'success': True, 'is_favorite': is_favorite}
    except Exception as err:
        payload = {'success': False}
    return ajax_answer_lazy(payload)


def read_message(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        msg = Message.objects.get(id=object_id)
        msg.read_at = now()
        msg.save()

        payload = dict(success=True)
    except Exception as err:
        logger.error(f'Read message error: {err}')
        payload = dict(success=False, err=err)
    return ajax_answer_lazy(payload)


def push_message(request, pk):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        recipient = get_user_model().objects.get(pk=pk)
        if recipient == request.user:
            raise AccessError
        subject = request.POST.get('subject')
        if not subject:
            subject = _('no subject')
        body = request.POST.get('message') or None
        if body is None:
            raise AccessError
        msg = Message()
        msg.subject = subject
        msg.ip = request.META['REMOTE_ADDR']
        msg.user_agent = request.META['HTTP_USER_AGENT']
        msg.body = body
        msg.sender = request.user
        msg.recipient = recipient
        msg.sent_at = now()
        msg.save()
        payload = dict(success=True, result=_(f'Message {recipient} sent successfully'))
        send_tg_user(recipient,
                     send_message_user.format(user=request.user,
                                              time=msg.sent_at.strftime("%d.%m.%Y %H:%M"),
                                              subject=subject,
                                              message=body[:100]))
    except AccessError as aerr:
        payload = dict(success=False, error=_('Unable to send message'))
    except Exception as err:
        logger.error(f'Ajax Send message error: {err}')
        payload = dict(success=False)
    return ajax_answer_lazy(payload)


# TODO: понять целесообрасть и убрать
def computing_recipe(request):
    try:
        if not request.user.is_authenticated:
            raise AccessError
    except AccessError as aerr:
        payload = dict(success=False, error=_('Unable computing recipe'))
    except Exception as err:
        logger.error(f'Ajax computing recipe error: {err}')
        payload = dict(success=False)
    return ajax_answer_lazy(payload)


def device_delete(request, object_id):
    try:
        usr = request.user
        if not usr.is_authenticated:
            raise AccessError
        device = get_object_or_404(ConnectedDevice, pk=object_id)
        if device.user == usr or usr.is_superuser:
            logs = device.devicedatalog_set.all()
            logs.delete()
            if hasattr(usr, 'device_on_dashboard') and usr.device_on_dashboard == device:
                usr.device_on_dashboard = None
                usr.save()
            device.enabled = False
            device.active = False
            device.save()
            cache.delete(device.token)
            payload = {'success': True,
                       'result': _(f'Device successfully removed'),
                       'device': f'device-{device.pk}'}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete device')}
        logger.error(f'Ajax delete device AccessError: '
                     f'user: {request.user.username}, '
                     f'device: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete device: {err}, user: {request.user.username}, device: {object_id}')
        payload = {'success': False, 'error': _('Error deleted device')}
    return ajax_answer_lazy(payload)


def module_delete(request, object_id):
    try:
        usr = request.user
        if not usr.is_authenticated:
            raise AccessError
        module = get_object_or_404(Modules, pk=object_id)
        if module.user == usr or usr.is_superuser:
            module_pk = module.pk
            logs = module.moduledatalog_set.all()
            logs.delete()
            # module.enabled = False
            # module.active = False
            # module.save()
            module.delete()
            cache.delete(module.token)
            payload = {'success': True,
                       'result': _(f'Module successfully removed'),
                       'device': f'module-{module_pk}'}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete module')}
        logger.error(f'Ajax delete module AccessError: '
                     f'user: {request.user.username}, '
                     f'module: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete module: {err}, user: {request.user.username}, module: {object_id}')
        payload = {'success': False, 'error': _('Error deleted module')}
    return ajax_answer_lazy(payload)


def device_status(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        device = get_object_or_404(ConnectedDevice, pk=object_id)
        if device.user == request.user or request.user.is_superuser:
            status = request.POST.get('dev_active', False)
            if status == 'on':
                status = True
                result = _(f'Device {device.name} active')
            else:
                status = False
                result = _(f'Device {device.name} is not active')
                cache.delete(device.token)
            device.active = status
            device.save()
            payload = {'success': True,
                       'result': result,
                       'status': device.active}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot change the device status')}
        logger.error(f'Ajax change status device AccessError: '
                     f'user: {request.user.username}, '
                     f'device: {object_id}')
    except Exception as err:
        logger.error(f'Ajax change status device: {err}, user: {request.user.username}, device: {object_id}')
        payload = {'success': False, 'error': _('Error change status')}
    return ajax_answer_lazy(payload)


def get_recipe_chart(request, slug):
    try:
        # if not request.user.is_authenticated and not request.user.is_pro:
        #     raise AccessError
        recipe = get_object_or_404(Recipe, slug=slug)
        if hasattr(recipe, 'recipedatalog'):
            result = recipe.recipedatalog.data
            return HttpResponse(result, content_type="application/json")
    except Exception as err:
        logger.error(f'Ajax get log device: {err}, user: {request.user.username}')
        payload = {'success': False, 'error': 'Error get log data', 'err': err}
        return ajax_answer_lazy(payload)


def get_link_login_bot(request):
    try:
        usr = request.user
        if not usr.is_authenticated and not usr.is_pro:
            raise AccessError
        key = secrets.token_urlsafe()
        payload = {'success': True,
                   'url': f'https://t.me/{settings.TELEGRAM_BOT_NAME}?start={key}'}
        cache.add(key, usr.id, 1800)
    except Exception as err:
        logger.error(f'Get Telegram Bot error: {err}, user: {request.user.username}')
        payload = {'success': False, 'error': 'Error get Telegram Bot URL', 'err': err}
    return ajax_answer_lazy(payload)


def set_recipe_visibility(request, slug):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        recipe = get_object_or_404(Recipe, slug=slug)
        if recipe.user != request.user:
            raise AccessError
        v = recipe.private
        recipe.private = not v
        recipe.save()
        payload = {'success': True, 'private': recipe.private}
        return ajax_answer_lazy(payload)
    except Exception as err:
        logger.error(f'Ajax error set visibility: {err}, User: {request.user.username}, Recipe: {recipe.name}')
        payload = {'success': False, 'error': 'Error set visibility', 'err': err}
        return ajax_answer_lazy(payload)


def user_image_attach(request, content_type, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        ctype = ContentType.objects.get_for_id(int(content_type))
        obj = ctype.get_object_for_this_type(pk=int(object_id))
        if obj.id != request.user.id and not request.user.is_superuser:
            raise AccessError
        pics = Pic.objects.filter(content_type__pk=ctype.pk, object_id=obj.id)
        if len(pics) >= setting('IMG_MAX_PER_USER', 5):
            raise AccessError
        upload = os.path.join(settings.MEDIA_ROOT, 'img')
        uploader = AjaxUploader(filetype='image', upload_dir=upload,
                                size_limit=setting('MAX_UPLOAD_IMAGE_SIZE', 1024000))
        result = uploader.handle_upload(request)
        if result['success']:
            new_img = Pic()
            new_img.content_type = ctype
            new_img.object_id = int(object_id)
            new_img.description = result['old_filename']
            new_img.user = request.user
            new_img.primary = True
            new_img.created_date = now()
            imgfile = result['filepath']
            new_img.img.save(result['filename'], File(open(imgfile, 'rb')))
            try:
                addons = dict(html=render_to_string('user/logo.html', {'user': request.user}))
            except:
                addons = dict()
            result.update(addons)
        return ajax_answer_lazy(result)
    except AccessError:
        payload = {'success': False, 'error': _('You are not allowed for add image')}
    except Exception as err:
        logger.error(f'Error user image attach: {err}')
        payload = {'success': False, 'error': err}
    return ajax_answer_lazy(payload)


def logo_delete(request):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        p = get_object_or_404(Pic, pk=request.POST.get('pk'))
        remove_thumbnails(p.img.path)
        remove_file(p.img.path)
        p.delete()
        html = render_to_string('user/logo.html', {'user': request.user})
        payload = {'success': True, 'html': html}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete images')}
    except Exception as err:
        logger.error(f'Error image delete: {err}')
        payload = {'success': False, 'error': err}
    return ajax_answer_lazy(payload)


def tg_receive_notif(request):
    try:
        usr = request.user
        if not usr.is_authenticated:
            raise AccessError
        if usr.available_telegram:
            acc = UserTelegramProfile.objects.get(user=usr.pk)
            notif = request.POST.get('tg_notif', False)
            if notif == 'on':
                acc.receive_notification = True
                result = _(f'Receive notification active')
            else:
                acc.receive_notification = False
                result = _(f'Receive notification is not active')
            acc.save()
            payload = {'success': True,
                       'result': result,
                       'status': acc.receive_notification}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot change the receive notification')}
        logger.error(f'Ajax change receive notification AccessError: '
                     f'user: {request.user.username}')
    except Exception as err:
        logger.error(f'Ajax change status receive notification: {err}, user: {request.user.username}')
        payload = {'success': False, 'error': _('Error change parameter receive notification')}
    return ajax_answer_lazy(payload)


def user_water_delete(request, object_id):
    try:
        usr = request.user
        if not usr.is_authenticated:
            raise AccessError
        water = get_object_or_404(WaterUserProfile, pk=object_id)
        if water.user == usr or usr.is_superuser:
            water.delete()
            payload = {'success': True,
                       'result': _(f'User water profile successfully removed'),
                       'waterID': object_id}
            action.send(request.user,
                        verb=_(f'User {usr.username} delete User water profile'),
                        action_type=ACTION_DELETED,
                        description=_(f'User {request.user.username} delete User water profile {object_id}'),
                        target=usr,
                        request=request)
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete water profile')}
        logger.error(f'Ajax delete user water profile AccessError: '
                     f'user: {request.user.username}, '
                     f'water profile: {object_id}')
    except Exception as err:
        logger.error(f'Ajax delete user water profile: {err}, user: {request.user.username}, water profile: {object_id}')
        payload = {'success': False, 'error': _('Error deleted user water profile')}
    return ajax_answer_lazy(payload)


def get_temp_url_recipe(request):
    try:
        usr = request.user
        if not usr.is_authenticated:
            raise AccessError
        slug = request.GET.get('rcp', None)
        if slug is None:
            raise Exception('slug is missing')
        recipe = get_object_or_404(Recipe, slug=slug)
        if recipe.user != request.user:
            raise AccessError
        url = recipe.create_temp_full_link()
        payload = {'success': True, 'url': url}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot get recipe link')}
    except Exception as err:
        logger.error(f'Error get temp link recipe: {err}, user: {request.user.username}')
        payload = {'success': False, 'error': _('Error get full link')}
    return ajax_answer_lazy(payload)


def delete_temp_url_recipe(request):
    try:
        usr = request.user
        if not usr.is_authenticated:
            raise AccessError
        slug = request.GET.get('rcp', None)
        if slug is None:
            raise Exception('slug is missing')
        recipe = get_object_or_404(Recipe, slug=slug)
        if recipe.user != request.user:
            raise AccessError
        k = getattr(recipe, 'accesskeyfullrecipe', None)
        if k is not None:
            k.delete()
        payload = {'success': True}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete recipe link')}
    except Exception as err:
        logger.error(f'Error delete temp link recipe: {err}, user: {request.user.username}')
        payload = {'success': False, 'error': _('Error delete full link')}
    return ajax_answer_lazy(payload)


def equipment_save(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        equipment = get_object_or_404(EquipmentModules, pk=object_id)
        mode = equipment.type
        if equipment.user == request.user or request.user.is_superuser:
            main_id = request.POST.get('equip_module_1', '')
            old_main = equipment.main
            if main_id:
                main = get_object_or_404(Modules, pk=int(main_id))
                if old_main:
                    if old_main != main:
                        old_main.mode = MODULE_OM_NONE
                        old_main.save()
                        equipment.main = main
                        main.mode = MODE_MATCHING[mode][0]
                        main.save()
                else:
                    equipment.main = main
                    main.mode = MODE_MATCHING[mode][0]
                    main.save()
            else:
                if old_main:
                    old_main.mode = MODULE_OM_NONE
                    old_main.save()
                    equipment.main = None
            second_id = request.POST.get('equip_module_2', '')
            old_second = equipment.second
            if second_id:
                second = get_object_or_404(Modules, pk=int(second_id))
                if old_second:
                    if old_second != second:
                        old_second.mode = MODULE_OM_NONE
                        old_second.save()
                        equipment.second = second
                        second.mode = MODE_MATCHING[mode][1]
                        second.save()
                else:
                    equipment.second = second
                    second.mode = MODE_MATCHING[mode][1]
                    second.save()
            else:
                if old_second:
                    old_second.mode = MODULE_OM_NONE
                    old_second.save()
                    equipment.second = None
            third_id = request.POST.get('equip_module_3', '')
            old_third = equipment.third
            if third_id:
                third = get_object_or_404(Modules, pk=int(third_id))
                if old_third:
                    if old_third != third:
                        old_third.mode = MODULE_OM_NONE
                        old_third.save()
                        equipment.third = third
                        third.mode = MODE_MATCHING[mode][2]
                        third.save()
                else:
                    equipment.third = third
                    third.mode = MODE_MATCHING[mode][2]
                    third.save()
            else:
                if old_third:
                    old_third.mode = MODULE_OM_NONE
                    old_third.save()
                    equipment.third = None
            fourth_id = request.POST.get('equip_module_4', '')
            old_fourth = equipment.fourth
            if fourth_id:
                fourth = get_object_or_404(Modules, pk=int(fourth_id))
                if old_fourth:
                    if old_fourth != fourth:
                        old_fourth.mode = MODULE_OM_NONE
                        old_fourth.save()
                        equipment.fourth = fourth
                        fourth.mode = MODE_MATCHING[mode][3]
                        fourth.save()
                else:
                    equipment.fourth = fourth
                    fourth.mode = MODE_MATCHING[mode][3]
                    fourth.save()
            else:
                if old_fourth:
                    old_fourth.mode = MODULE_OM_NONE
                    old_fourth.save()
                    equipment.fourth = None
            equipment.save()
            payload = {'success': True,
                       'ready': equipment.is_ready,
                       'result': _(f'Settings {equipment.name} saved')}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot change the equipment')}
        logger.error(f'Ajax change equipment AccessError: '
                     f'user: {request.user.username}, '
                     f'device: {object_id}')
    except Exception as err:
        logger.error(f'Ajax change equipment: {err}, user: {request.user.username}, device: {object_id}')
        payload = {'success': False, 'error': _('Error save equipment')}
    return ajax_answer_lazy(payload)


def equipment_status(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        equipment = get_object_or_404(EquipmentModules, pk=object_id)
        if equipment.user == request.user or request.user.is_superuser:
            status = request.GET.get('active', 'false')
            if status == 'true':
                equipment.active = True
            else:
                equipment.active = False
            equipment.save()
            payload = {'success': True,
                       'active': equipment.active,
                       'result': _(f'Settings {equipment.name} saved')}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot change the equipment')}
        logger.error(f'Ajax change equipment AccessError: '
                     f'user: {request.user.username}, '
                     f'device: {object_id}')
    except Exception as err:
        logger.error(f'Ajax error change status equipment: {err}, user: {request.user.username}, equipment ID: {object_id}')
        payload = {'success': False, 'error': _('Error change status equipment')}
    return ajax_answer_lazy(payload)


def equipment_reset(request, object_id):
    """
    Clear module data log
    """
    try:
        if not request.user.is_authenticated:
            raise AccessError
        equipment = get_object_or_404(EquipmentModules, pk=object_id)
        if equipment.user == request.user or request.user.is_superuser:
            equipment.active = False
            if equipment.main:
                m = equipment.main.moduledatalog_set.all()
                if m:
                    m.delete()
            if equipment.second:
                s = equipment.second.moduledatalog_set.all()
                if s:
                    s.delete()
            if equipment.third:
                t = equipment.third.moduledatalog_set.all()
                if t:
                    t.delete()
            if equipment.fourth:
                f = equipment.fourth.moduledatalog_set.all()
                if f:
                    f.delete()
            equipment.save()
            payload = {'success': True,
                       'active': equipment.active,
                       'result': _(f'Settings {equipment.name} reset')}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot settings reset the equipment')}
        logger.error(f'Ajax reset equipment AccessError: '
                     f'user: {request.user.username}, '
                     f'module: {object_id}')
    except Exception as err:
        logger.error(f'Ajax error reset equipment: {err}, user: {request.user.username}, equipment ID: {object_id}')
        payload = {'success': False, 'error': _('Error reset equipment')}
    return ajax_answer_lazy(payload)


def module_full_reset(request):
    payload = {}
    try:
        if not request.user.is_authenticated:
            raise AccessError
        token = request.GET.get('tkn', '')
        if token:
            try:
                module = Modules.objects.get(token=token)
                module.mode = MODULE_OM_NONE
                main = getattr(module, 'main', None)
                if main is not None:
                    main.active = False
                    main.main = None
                    main.save()
                second = getattr(module, 'second', None)
                if second is not None:
                    second.active = False
                    second.second = None
                    second.save()
                third = getattr(module, 'third', None)
                if third is not None:
                    third.active = False
                    third.third = None
                    third.save()
                fourth = getattr(module, 'main', None)
                if fourth is not None:
                    fourth.active = False
                    fourth.fourth = None
                    fourth.save()
                module.save()
                payload = {'success': True}
            except Modules.DoesNotExist:
                payload = {'status': 'error', 'error': 'Module not found'}
        else:
            payload = {'status': 'error', 'error': 'Module not found'}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot reset the module')}
        logger.error(f'Ajax reset module AccessError: '
                     f'user: {request.user.username}, '
                     f'module: {token}')
    except Exception as err:
        logger.error(f'Ajax error full reset module: {err}, user: {request.user.username}, module token: {token}')
        payload = {'success': False, 'error': _('Error full reset module')}
    return ajax_answer_lazy(payload)

