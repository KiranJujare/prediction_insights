from django.conf.urls import include, url
from django.conf.urls import patterns
from django.contrib import admin
import views

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'insights_engine.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^home/$', views.index),
    url(r'^home/get_by_field/$', views.get_by_field),
    url(r'^home/get_lat_long_by_field/$', views.get_lat_long_by_field),
    url(r'^home/get_default_top_listings/$', views.get_default_top_listings),
    url(r'^admin/', include(admin.site.urls)),
]

from django.conf import settings
import os

if settings.DEBUG404:
    urlpatterns += patterns('',
                            (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                             {'document_root': os.path.join(os.path.dirname(__file__), 'static')} ),
    )