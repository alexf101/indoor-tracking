from django.conf.urls import patterns, include, url
from django.shortcuts import redirect
from rest_framework import routers
from FingerprintsREST.OptionalSlashRouter import OptionalSlashRouter
from FingerprintsREST.views import BaseStationAPI, ScanViewAPI, DocsAPI, DeviceAPI
from FingerprintsREST.views import UserAPI, GroupAPI, BuildingAPI, FingerprintAPI, LocationAPI
# Custom Rest ViewSet URLs
from FingerprintsREST.views.MatchLocation import MyLocation

router = OptionalSlashRouter()
router.register(r'(?i)auth_users/?', UserAPI.AdminUserViewSet)
router.register(r'(?i)devices/?', DeviceAPI.DeviceViewSet)
router.register(r'(?i)groups/?', GroupAPI.GroupViewSet)
router.register(r'(?i)scans/?', ScanViewAPI.ScanViewSet)
router.register(r'(?i)buildings/?', BuildingAPI.BuildingViewSet)
router.register(r'(?i)fingerprints/?', FingerprintAPI.FingerprintViewSet)
router.register(r'(?i)base_stations/?', BaseStationAPI.BaseStationViewSet)
router.register(r'(?i)locations/?', LocationAPI.LocationViewSet)

urlpatterns = patterns('',
    # Rest required URLs
    url(r'^', include(router.urls)),
    url(r'^(?i)api/', include('rest_framework.urls', namespace='rest_framework')),
    # Other custom Rest URLs
#    url(r'^fingerprints/?$', FingerprintAPI.FingerprintViewSet.as_view()),
#    url(r'^fingerprints/(?P<pk>[0-9]+)/?$', FingerprintAPI.FingerprintViewSet.as_view()),
    url(r'^(?i)users/?$', UserAPI.CreateOrList.as_view()),
    url(r'^(?i)users/(?P<pk>[0-9]+)/?$', UserAPI.RetrieveUpdateOrDestroy.as_view(), name='user-detail'),
    url(r'^(?i)mylocation/(?P<limit>[0-9]+)/?$', MyLocation.retrieve),
    url(r'^(?i)mylocation/?$', MyLocation.retrieve, kwargs=dict(limit=1), name='retrieve_my_location'),
    url(r'^(?i)confirm/(?P<location_pk>[0-9]+)/(?P<fingerprint_pk>[0-9]+)/?$', MyLocation.confirm),
    url(r'^(?i)confirm/(?P<fingerprint_pk>[0-9]+)/?$', MyLocation.confirm),
    url(r'^(?i)docs-api/?', DocsAPI.ApiDocumentation.as_view()),
    url(r'^(?i)docs/?$', include('rest_framework_docs.urls')),
    url(r'^(?i)custom/location/?$', LocationAPI.post_or_get_location, name='post_or_get_location'),
    url(r'^(?i)getCSV/?$', MyLocation.getCSV, name='getCSV'),
    url(r'^', lambda request: redirect('api-documentation')),
)