import urllib
from django.core.cache import cache
from rest_framework import serializers, status
from FingerprintsREST.models import Fingerprint, BaseStation, Scan, Location, Device
from FingerprintsREST.views.ScanViewAPI import ScanSerializer
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, GenericAPIView, ListAPIView, RetrieveAPIView, DestroyAPIView
from rest_framework.response import Response
from OwnedViews import OwnedViewSet, OwnedViewSerializer
import logging

log = logging.getLogger(__name__)


def createFingerprint(data, owner):
    '''
    Creates a fingerprint from data in the form:
    {
        'field1'...
        'scans': [{'base_station': {}}, {}, {}]
    }
    :param data:
    :return: fingerprint
    :rtype: Fingerprint
    '''
    # some dictionary elements need to be created or removed before
    # the dictionary can be passed into the fingerprint constructor
    device = data.get('device')
    if device is not None:
        try:
            data['device'] = Device.objects.get(name=device)
        except Device.DoesNotExist:
            data['device'] = Device.objects.create(name=device)
    scans = data['scans']
    del data['scans']
    if data.get('id') is not None:
        del data['id']  # just in case, this should be read-only anyway!
    location_str = data.get('location')
    if location_str is not None:
        del data['location']
        if "locations/" in location_str:
            start_pos = location_str.index("locations/") + 10
            if location_str[-1] == "/":
                location_id = int(location_str[start_pos:-1])
            else:
                location_id = int(location_str[start_pos:])
            print "Location id: " + str(location_id)
        else:
            location_id = int(location_str)
        fingerprint = Fingerprint.objects.create(owner=owner, location_id=location_id, confirmed=True, **data)
    else:
        fingerprint = Fingerprint.objects.create(owner=owner, **data)
    log.debug("Created fingerprint, id = " + str(fingerprint.pk))
    for scan in scans:
        base_station = scan['base_station']
        bssid = base_station['bssid']
        freq = base_station['frequency']
        ssid = base_station['ssid']
        try:
            scan['base_station'] = BaseStation.objects.get(bssid=bssid, frequency=freq)
        except BaseStation.DoesNotExist:
            scan['base_station'] = BaseStation.objects.create(owner=owner, bssid=bssid, frequency=freq)
        # update ssid
        if scan['base_station'].ssid != ssid:
            log.debug("Updating ssid for "+bssid+" from "+scan['base_station'].ssid+" to "+ssid)
            scan['base_station'].ssid = ssid
            scan['base_station'].save()
        Scan.objects.create(fingerprint=fingerprint, **scan)
    fingerprint_changed(fingerprint)
    return fingerprint


def fingerprint_changed(fingerprint):
    """
    :type fingerprint: Fingerprint
    :param fingerprint:
    """
    try:
        loc = fingerprint.location
    except:
        loc = None
    if loc is not None:
        update_model(fingerprint)


def update_model(fingerprint):
    cache_key = urllib.quote(fingerprint.location.building.name)
    model = cache.get(cache_key)
    if model is not None:
        model.add_fingerprint(fingerprint)
        cache.set(cache_key, model)


class FingerprintSerializerUnowned(serializers.ModelSerializer):
    scans = ScanSerializer(many=True)

    class Meta:
        model = Fingerprint


class FingerprintViewSerializer(OwnedViewSerializer):
    scans = ScanSerializer(many=True)
    device = serializers.SlugRelatedField(required=False, slug_field='name')
    id = serializers.Field()

    class Meta:
        model = Fingerprint


class FingerprintViewSet(OwnedViewSet):
    """
    Fingerprints record the set of received signal strength indicators (RSSI) at a particular location at a particular
    time (and according to a particular device).

    In addition, the magnetic field properties of that location (at that time, according to that device) are also
    recorded, including device orientation.

    location -- The location must already exist and is provided in URL form
    confirmed -- Whether or not the fingerprint's location has been confirmed as the correct one. When a fingerprint is submitted in order to predict a location, it is recorded with confirmed as false. When a fingerprint is submitted along with a location, confirmed is set to true. The 'confirm' message can also be sent to set confirmed to true.
    scans -- A list [] of base_stations along with levels. For convenience, the base_stations are not set as hyperlinked fields, but directly from the data, e.g. {..., 'scans': ['base_station': {'bssid': '...', 'ssid': '...', 'frequency': 2247 }, 'level': -63]} ..., } New base_station objects will be created as necessary, owned by the fingerprint submitter.
    device -- The name of a device, e.g. HTC Sensation XL or iPhone 4S
    timestamp -- YYYY-MM-DD
    """
    queryset = Fingerprint.objects.all()
    serializer_class = FingerprintViewSerializer

    def create(self, request, *args, **kwargs):
        log.debug("CREATING A FINGERPRINT")
        log.debug(str(request.DATA))
        fingerprint_dic = {}
        for k, v in request.DATA.iteritems():
            fingerprint_dic[k] = v
        fingerprint = createFingerprint(fingerprint_dic, request.user)
        fingerprint.confirmed = True
        fingerprint.save()
        serial = FingerprintViewSerializer(fingerprint, context={'request': request})
        return Response(data=serial.data, status=201)


