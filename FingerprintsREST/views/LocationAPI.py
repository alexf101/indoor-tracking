from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from FingerprintsREST.models import Location, Building
from OwnedViews import OwnedViewSet, OwnedViewSerializer
from logging import getLogger


class LocationViewSerializer(OwnedViewSerializer):
    id = serializers.Field()

    class Meta:
        model = Location


class LocationViewSet(OwnedViewSet):
    """
    The location's name, within the building, should be unique.
    """
    queryset = Location.objects.all()
    serializer_class = LocationViewSerializer


# I'm not sure why this post or create pattern isn't integrated into the framework,
# as it's actually more idempotent and safe from race conditions.

log = getLogger(__name__)

@api_view(['POST'])
def post_or_get_location(request):
    try:
        name = request.DATA['name']
        room = request.DATA['room']
        building_dict = request.DATA['building_obj']
        building_name = building_dict['name']
        description = request.DATA['description']
        log.debug("Post or get for location: "+str(request.DATA))
        try:
            building = Building.objects.get(name=building_name)
        except:
            log.debug("New building")
            building = Building.objects.create(name=building_name, owner=request.user)
        try:
            location = Location.objects.get(name=name, building=building)
        except:
            log.debug("New location")
            location = Location.objects.create(name=name, building=building, owner=request.user, room=room)
        location.description = description
        location.save()
        return Response(LocationViewSerializer(location).data)
    except Exception, e:
        log.exception(e)
        return HttpResponse("failure")
