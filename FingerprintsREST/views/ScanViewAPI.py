from rest_framework import viewsets, serializers
from FingerprintsREST.models import Scan, BaseStation
from FingerprintsREST.views.BaseStationAPI import BaseStationViewSerializer, BaseStationViewSerializerWithoutOwner
import logging
from FingerprintsREST.views.CustomViewSets import QueryableViewSet

log = logging.getLogger(__name__)


class ScanSerializer(serializers.ModelSerializer):  # Hyperlinked
    #base_station = serializers.HyperlinkedIdentityField(BaseStation)  # BaseStationViewSerializer()
    base_station = BaseStationViewSerializerWithoutOwner()
    #base_station = serializers.Field(required=False, source='base_station.bssid')
    #base_station.owner = serializers.Field(source='owner.username')

    class Meta:
        model = Scan
        exclude = ['fingerprint', 'url', 'id']  # , 'id']


class ScanListSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Scan

#class ScanSerializer(serializers.ModelSerializer):  # Hyperlinked
#    #base_station = serializers.HyperlinkedIdentityField(BaseStation)  # BaseStationViewSerializer()
#    #base_station = BaseStationViewSerializer()
#    #base_station = serializers.Field()
#    #base_station.owner = serializers.Field(source='owner.username')
#
#    class Meta:
#        model = Scan
#        exclude = ['fingerprint', 'url', 'id']  # , 'id']
#        depth = 1


class ScanViewSet(QueryableViewSet):
    '''
    Scans are only altered through fingerprints. Each scan represents the RSSI (in dB) of one base_station,
    at the location and time specified by the referenced fingerprint.

    The owner of a scan is the owner of the fingerprint.

    These should never be created directly - instead post a fingerprint that includes scans.
    '''
    queryset = Scan.objects.all()
    serializer_class = ScanListSerializer

    def pre_save(self, obj):
        print "Scan pre-save"
        if self.request.user.is_authenticated():
            print obj
            log.debug(obj)
            obj.base_station.owner = self.request.user