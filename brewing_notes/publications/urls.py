from django.urls import path

from nnmware.core.ajax import flat_comment_add

from .ajax import *
from .views import *


urlpatterns = [
    path('publications/', TopicAllListView.as_view(), name='topic_list'),
    path('publications/topic/<slug:slug>/', TopicOneView.as_view(), name='topic_detail'),
    path('publications/topic/<slug:slug>/post/add/', PostAddView.as_view(), name='post_add'),

    path('api/v1/post/<str:content_type>/<str:object_id>/image/add/', post_image_attach, name='content_attach'),
    path('api/v1/post/<int:object_id>/delete/', post_delete, name='post_delete'),
    path('api/v1/image/delete/', image_delete, name='image_delete'),
]