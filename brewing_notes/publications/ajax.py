import logging
import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from nnmware.core.abstract import Pic
from nnmware.core.ajax import ajax_answer_lazy
from nnmware.core.constants import STATUS_DELETE
from nnmware.core.exceptions import AccessError
from nnmware.core.imgutil import remove_thumbnails, remove_file
from nnmware.core.utils import setting

from brew.ajax import AjaxUploader

from .models import Post


logger = logging.getLogger(__name__)


def post_image_attach(request, content_type, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        ctype = ContentType.objects.get_for_id(int(content_type))
        obj = ctype.get_object_for_this_type(pk=int(object_id))
        if obj.user != request.user and not request.user.is_superuser:
            raise AccessError
        pics = Pic.objects.filter(content_type__pk=ctype.pk, object_id=obj.id)
        if len(pics) >= setting('IMG_MAX_PER_OBJECT', 5):
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
            new_img.created_date = now()
            imgfile = result['filepath']
            new_img.img.save(result['filename'], File(open(imgfile, 'rb')))
        else:
            raise AccessError
        html = render_to_string('blocks/image_item.html', {'pic': new_img})
        payload = {'success': True, 'html': html}
    except AccessError:
        payload = {'success': False, 'error': _('You are not allowed for add image')}
    except Exception as err:
        logger.error(f'Error post image attach: {err}')
        payload = {'success': False, 'error': err}
    return ajax_answer_lazy(payload)


def pic_delete(pic_id):
    try:
        pic = Pic.objects.get(pk=pic_id)
        remove_thumbnails(pic.img.path)
        remove_file(pic.img.path)
        pic.delete()
        result = {'success': True}
    except Exception as err:
        logger.error(f'Error pic delete: {err}')
        result = {'success': False, 'error': err}
    return result


def image_delete(request):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        p = get_object_or_404(Pic, pk=request.POST.get('pk'))
        remove_thumbnails(p.img.path)
        remove_file(p.img.path)
        p.delete()
        payload = {'success': True}
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete images')}
    except Exception as err:
        logger.error(f'Error image delete: {err}')
        payload = {'success': False, 'error': err}
    return ajax_answer_lazy(payload)


def post_delete(request, object_id):
    try:
        if not request.user.is_authenticated:
            raise AccessError
        post = get_object_or_404(Post, pk=object_id)
        if post.user == request.user or request.user.is_moderator:
            pics = post.allpics
            post.pics = len(pics)
            if pics:
                for pic in pics:
                    remove_thumbnails(pic.img.path)
                    remove_file(pic.img.path)
                    pic.delete()
            post.status = STATUS_DELETE
            post.save()
            payload = {'success': True,
                       'post_id': post.pk,
                       'location': reverse_lazy('topic_detail', args=[post.topic.slug])}
        else:
            raise AccessError
    except AccessError:
        payload = {'success': False, 'error': _('You cannot delete images')}
    except Exception as err:
        logger.error(f'Error Post delete: {err}')
        payload = {'success': False, 'error': err}
    return ajax_answer_lazy(payload)
