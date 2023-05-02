import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import ListView, DetailView, CreateView
from django.views.generic.list import MultipleObjectMixin


from nnmware.core.constants import STATUS_PUBLISHED, STATUS_DELETE

from catalog.views import GetObjectMixin

from brew.tgbot.static_text import publication_add
from brew.tgbot.dispatch import send_tg_admins

from .models import Post, Topic


logger = logging.getLogger(__name__)


class TopicAllListView(LoginRequiredMixin, ListView):
    model = Topic
    login_url = '/login/'
    template_name = 'publications/topic_list.html'

    def get_queryset(self):
        result = self.model.objects.filter(enabled=True, rootnode=True).order_by('-position')
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['last_posts'] = Post.objects.active().order_by('-id')[:10]
        return context


class TopicOneView(LoginRequiredMixin, GetObjectMixin, DetailView, MultipleObjectMixin):
    model = Topic
    login_url = '/login/'
    context_object_name = 'topic'
    paginate_by = 20
    paginate_orphans = 3
    template_name = 'publications/topic_detail.html'

    def get_queryset(self):
        self.object = self.get_object()
        topics = self.object.obj_active_set.order_by('created_date')
        return topics

    def get_context_data(self, **kwargs):
        object_list = self.get_queryset()
        pages = Paginator(object_list, self.paginate_by, self.paginate_orphans)
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context


class PostAddView(LoginRequiredMixin, GetObjectMixin, CreateView):
    """
    Adding a comment to a topic
    """
    model = Post
    login_url = '/login/'
    paginate_by = 20
    paginate_orphans = 3

    def get_topic(self):
        return get_object_or_404(Topic, slug=self.kwargs['slug'])

    def get_success_url(self):
        topic = self.get_topic()
        url = reverse_lazy('topic_detail', args=[topic.slug])
        pages = Paginator(topic.obj_active_set, self.paginate_by, self.paginate_orphans)
        return f'{url}?page={pages.num_pages}'

    def post(self, request, *args, **kwargs):
        try:
            topic = self.get_topic()
            post_id = request.POST.get('post_id', '')
            body = request.POST.get('text', '')
            if post_id:
                p = self.model.objects.get(pk=post_id)
            else:
                p = self.model()
                p.user = request.user
                p.topic = topic
                p.status = STATUS_PUBLISHED
            p.description = body
            p.save()
            send_tg_admins(publication_add.format(user=request.user.username,
                                                  topic=topic.name,
                                                  post=body))
            messages.success(request, _('Post saved'))
        except Exception as err:
            logger.error(f'{self.__class__.__name__} Error saving post: {err}')
            messages.error(request, _(f'Error saving post'))
        return HttpResponseRedirect(self.get_success_url())


# class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
#         """
#         Delete post
#         """
#         model = Post
#         login_url = '/login/'
#         template_name = 'publications/topic_detail.html'
#
#         # def get_success_url(self):
#         #     return reverse_lazy('user_recipes', args=[self.request.user.username])
#
#         def get_object(self):
#             return get_object_or_404(self.model, slug=self.kwargs['object_id'])
#
#         def test_func(self):
#             self.object = self.get_object()
#             if self.request.user == self.object.user or self.request.user.is_moderator:
#                 return True
#             else:
#                 return False
#
#         def get(self, request, *args, **kwargs):
#             try:
#                 topic = self.get_object()
#                 pics = topic.allpics
#                 topic.pics = len(pics)
#                 topic.enabled = False
#                 topic.status = STATUS_DELETE
#                 topic.save()
#                 if pics:
#                     for pic in pics:
#                         remove_thumbnails(pic.img.path)
#                         remove_file(pic.img.path)
#                         pic.delete()
#                 messages.success(request, _(f'Post successfully deleted'))
#             except Exception as err:
#                 logger.error(f'Post delete error: {err}')
#                 messages.error(request, _('Post delete error'))
#             return HttpResponseRedirect(self.get_success_url())


    # def get_success_url(self):
    #     """ Redirect on last page with new comments"""
    #     object_id = self.kwargs['object_id']
    #     topic = get_object_or_404(self.model, id=object_id)
    #     url = reverse_lazy('topic_detail', args=[topic.slug])
    #     pages = Paginator(topic.comments, self.paginate_by, self.paginate_orphans)
    #     return f'{url}?page={pages.num_pages}'
    #
    # def post(self, request, *args, **kwargs):
    #     try:
    #         if not request.user.is_authenticated:
    #             raise AccessError
    #         content_type = self.kwargs['content_type']
    #         object_id = self.kwargs['object_id']
    #         comment = FlatNnmcomment()
    #         comment.user = request.user
    #         comment.content_type = ContentType.objects.get_for_id(int(content_type))
    #         comment.object_id = int(object_id)
    #         comment.ip = request.META['REMOTE_ADDR']
    #         comment.user_agent = request.META['HTTP_USER_AGENT']
    #         comment.comment = request.POST['comment']
    #         if not len(comment.comment):
    #             raise AccessError
    #         comment.save()
    #         action.send(request.user, verb=_('commented'), action_type=ACTION_COMMENTED,
    #                     description=comment.comment, target=comment.content_object, request=request)
    #     except AccessError as aerr:
    #         messages.error(request, _(f'You are not allowed for add comment'))
    #     except Exception as err:
    #         messages.error(request, _(f'Error adding a comment'))
    #     return HttpResponseRedirect(self.get_success_url())