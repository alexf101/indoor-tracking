from rest_framework.response import Response
from FingerprintsREST.models import Building
#from rest_framework import serializers
from OwnedViews import OwnedViewSet, OwnedViewSerializer


class BuildingViewSerializer(OwnedViewSerializer):
    #id = serializers.Field

    class Meta:
        model = Building


class BuildingViewSet(OwnedViewSet):
    """
    Represents a single area.

    name -- should be unique
    """
    queryset = Building.objects.all()
    serializer_class = BuildingViewSerializer
