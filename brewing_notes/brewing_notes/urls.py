"""brewing_notes URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.conf.urls import include, handler400, handler404, handler500, handler403
from django.urls import path

from brew.feed import RecipesFeed, TurboFeed
from brew.sitemap import RecipeSitemap


sitemaps = {
    'recipe': RecipeSitemap,
}

feed = TurboFeed()
feed.configure_analytics_yandex('71413033')
feed.configure_ad_yandex('R-A-1277742-3')

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('13bossmode13/', admin.site.urls),
    path('feed/', RecipesFeed()),
    path('feed/rss-turbo.xml', feed),
    path('', include('brew.urls')),
    path('', include('catalog.urls')),
    path('', include('publications.urls')),
    path('', include('logdata.urls')),
    path('', include('pantry.urls')),
    path('', include('docs.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

handler400 = 'brew.views.page_not_found'
handler403 = 'brew.views.page_not_found'
handler404 = 'brew.views.page_not_found'
handler500 = 'brew.views.page_500_error'

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
