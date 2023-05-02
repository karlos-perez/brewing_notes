from django.contrib.syndication.views import Feed
from django.template.loader import render_to_string
from django.urls import reverse

from yaturbo import YandexTurboFeed

from .models import Recipe


class RecipesFeed(Feed):
    link = '/recipes/public/'

    def title(self):
        return 'Ресурс в помощь пивовару: рецепты пива, ингредиенты, стили, калькуляторы.'

    def description(self):
        return 'Последние опубликованные рецепты пива'

    def items(self):
        return Recipe.objects.active()

    def item_title(self, item):
        return item.seo_title

    def item_description(self, item):
        return item.seo_description

    def item_link(self, item):
        return reverse('recipe_card', args=[item.uid])


class TurboFeed(YandexTurboFeed):
    title = 'Ресурс в помощь пивовару: рецепты пива, ингредиенты, стили, калькуляторы.'
    description = 'Последние опубликованные рецепты пива'
    link = '/recipes/public/'
    item_html = 'feeds/recipe_turbo.html'

    # turbo_sanitize = True

    def item_title(self, item):
        return ''

    def item_description(self, item):
        return ''

    def item_link(self, item):
        return reverse('recipe_card', args=[item.uid])

    def item_guid(self, item):
        return ''

    def items(self):
        return Recipe.objects.active()

    def item_turbo(self, item):
        return render_to_string(self.item_html, {'obj': item})
