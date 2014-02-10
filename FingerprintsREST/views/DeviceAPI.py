from rest_framework import serializers
from FingerprintsREST.models import Device
from FingerprintsREST.views.CustomViewSets import QueryableViewSet
from OwnedViews import OwnedViewSet, OwnedViewSerializer


class DeviceViewSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Device


class DeviceViewSet(QueryableViewSet):
    """
    The location's name, within the building, should be unique.
    """
    queryset = Device.objects.all()
    serializer_class = DeviceViewSerializer