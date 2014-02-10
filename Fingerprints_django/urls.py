from django.conf import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import FingerprintsREST.urls as rest_urls
import Fingerprints_front.urls as front_urls

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Fingerprints_django.views.home', name='home'),
    # url(r'^Fingerprints_django/', include('Fingerprints_django.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(rest_urls)),
    url(r'^', include(front_urls)),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }), # only required for development server, but should never be reached in production so may as well leave it in
)
