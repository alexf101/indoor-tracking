from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Fingerprints_django.views.home', name='home'),

    url(r'^$', views.home),
    url(r'^home/?$', views.home, name='home'),
    url(r'^how_to_use_api/?$', views.how_to_use_api, name='how_to_use_api'),
    url(r'^client_libs/?$', views.client_libs, name='client_libs'),
    url(r'^applications/?$', views.applications, name='applications'),
    url(r'^contact/?$', views.contact, name='contact'),
    url(r'^(?P<url>.*)$', views.not_found, name='not_found'),
)
