from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from nnmware.core.admin import TreeAdmin

from .models import Topic, Post


@admin.register(Topic)
class TopicAdmin(TreeAdmin):
    fieldsets = (
        (_("Main"), {"fields": [("name", "slug"), ("parent", "login_required",), ('status', 'permission')]}),
        (_("Description"), {"classes": ("collapse",),
                            "fields": [("description",), ("position", "rootnode")]}),
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Main'), {'fields': [('id', 'user', 'enabled', 'topic')]}),
        (_('Content'), {'fields': [('name', 'status'), ('description',)]}),
        (_('Meta'), {'fields': [('created_date', 'updated_date')]}),
    )
    list_display = ('user', 'created_date', 'name', 'status')
    list_filter = ('created_date',)
    date_hierarchy = 'created_date'
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_date', 'updated_date', 'id')