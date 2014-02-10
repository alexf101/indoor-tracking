from rest_framework import serializers
from FingerprintsREST.models import BaseStation
from OwnedViews import OwnedViewSet, OwnedViewSerializer


class BaseStationViewSerializer(OwnedViewSerializer):
    #owner = serializers.Field(source='owner.username')
    #owner = serializers.RelatedField(required=False)
    class Meta:
        model = BaseStation


class BaseStationViewSerializerWithoutOwner(OwnedViewSerializer):
    #owner = serializers.Field(source='owner.username')
    #owner = serializers.RelatedField(required=False)
    class Meta:
        model = BaseStation
        exclude = ['owner']


class BaseStationViewSet(OwnedViewSet):
    """
    Represents a single access point or base station.

    The combination of bssid and frequency must be unique, but the ssid is not unique and may change.

    The intention is that Base Station's will be created through fingerprints, not through POSTs - however
    if an SSID changes then it may be preferable to PUT the change through here.

    bssid -- The basic service set identifier of this physical access point
    ssid -- The service set identifier of the network
    frequency -- The frequency band at which it is transmitting
    """
    queryset = BaseStation.objects.all()
    serializer_class = BaseStationViewSerializer