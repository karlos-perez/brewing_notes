from django.conf import settings
from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from nnmware.core.abstract import Tree, AbstractDate, AbstractName, PicsMixin
from nnmware.core.constants import STATUS_UNKNOWN, STATUS_CHOICES
from nnmware.core.managers import StatusManager
from nnmware.core.models import LikeMixin, ContentBlockMixin, FlatNnmcomment

from brew.constants import STATUS_USER, USER


class Topic(Tree):
    status = models.IntegerField(_("Status"), choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    permission = models.IntegerField(_("Permission user"), choices=STATUS_USER, default=USER)

    class Meta:
        ordering = ['parent__id', 'name']
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    @property
    def obj_active_set(self):
        return Post.objects.active().filter(topic=self)


class Post(AbstractDate, AbstractName, LikeMixin,  ContentBlockMixin):
    topic = models.ForeignKey(Topic, verbose_name=_('Topic'), null=True, blank=True, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'), on_delete=models.PROTECT)
    status = models.IntegerField(_("Status"), choices=STATUS_CHOICES, default=STATUS_UNKNOWN)

    objects = StatusManager()

    class Meta:
        ordering = ['-created_date', ]
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def get_absolute_url(self):
        return reverse('topic_detail', args=[self.pk])

    # @property
    # def comments(self):
    #     return FlatNnmcomment.objects.for_object(self).order_by('created_date')

