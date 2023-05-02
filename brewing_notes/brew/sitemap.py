from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Recipe


class RecipeSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def lastmod(self, obj):
        return obj.updated_date

    def items(self):
        return Recipe.objects.active()

    def location(self, item):
        return reverse('recipe_card', args=[item.uid])
