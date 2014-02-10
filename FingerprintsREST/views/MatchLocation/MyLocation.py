from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import logging
import urllib
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from FingerprintsREST.models import Fingerprint, Scan, Location
from FingerprintsREST.utils import log_task_start, log_task_end
from FingerprintsREST.views.FingerprintAPI import createFingerprint, update_model
from FingerprintsREST.views.LocationAPI import LocationViewSerializer
from FingerprintsREST.views.MatchLocation.Learning import Tracker, ScikitModel
from predictors import *
from cPickle import load
import os


log = logging.getLogger(__name__)
#weakest_signal = min(Scan.objects.all().aggregate(Min("level")), -101)
#cache.add("weakest_signal", weakest_signal)  # add creates the key only if it does not already exist
cached_tracker = {}  # tracker, time_modified

@api_view(['POST'])
def retrieve(request, limit):
    """
    Guesses the location at which the fingerprint was taken, and saves the fingerprint.

    If the limit argument is supplied, up to that number of results will be returned, in a list
    ordered by probability. Otherwise, limit defaults to 1.

    The parameters of the returned message are 'locations', and 'fingerprint_id'.

    {
        'locations': [best_matching_location, second_best_location,..., limit_matching_location],
        'fingerprint_id': fingerprint_id   // of the fingerprint that you sent
    }

    fingerprint -- A new fingerprint (see /fingerprints/)

    """
    log_task_start("Find current location request")
    limit = int(limit)
    f_dict = request.DATA['fingerprint']
    fingerprint = createFingerprint(f_dict, request.user)
    building_name = request.DATA['building']
    tracker = getTracker(building_name)
    if tracker is None:
        return Response(data={'detail': "Server is still loading data for that building... This usually occurs if "
                                        "the server had to be restarted for some reason. Please wait a few minutes "
                                        "and try again"},
                        status=503)  # 503 Service Unavailable
    if limit > 1:
        locations_ordered_by_prob = tracker.guess_all(fingerprint)
        log.debug("location id's ordered by prob: " + str(locations_ordered_by_prob))
        # turn the pk's into locations
        locations_ordered_by_prob = map(lambda location_pk: Location.objects.get(pk=location_pk), locations_ordered_by_prob)
        # locations_prob_tuples.sort(key=lambda tup: tup[1])
        # log.debug("Tuples prob sorting: " + str(locations_prob_tuples))
        # locations_ordered_by_prob = map(lambda tup: tup[0], locations_prob_tuples)
    else:
        location = tracker.guess(fingerprint)
        location_obj = Location.objects.get(pk=location)
        locations_ordered_by_prob = [location_obj]
    log.debug("locations ordered by prob: " + str(locations_ordered_by_prob))
    try:
        fingerprint.location = locations_ordered_by_prob[0]
    except:
        log.warn("No locations found")
        pass
    fingerprint.save()
    # return the ordered list of locations, and an id for the new fingerprint
    if limit <= 1:
        log.debug("Invalid limit: "+str(limit))
        limit = 1
    serial = LocationViewSerializer(locations_ordered_by_prob[:limit], context={'request': request}, many=True)
    response_data = {'locations': serial.data, 'fingerprint_id': fingerprint.pk}
    # log.debug("response: "+str(response_data))  # remove me; verbose
    log_task_end("Find current location request")
    return Response(data=response_data)


@api_view(['PUT'])
def confirm(request, fingerprint_pk, location_pk=-1):
    """Allows a kind client to confirm that the location sent was correct,
or alternatively send a new location for the fingerprint. This will cause
the building learning model to be updated to include the confirmed fingerprint,
improving performance for the user.

    If the location pk is not known, it can be determined if a location object is provided in the request body."""
    log_task_start("Confirm location request")
    stored_fingerprint = Fingerprint.objects.get(pk=fingerprint_pk)
    if not request.user.is_authenticated() or not request.user == stored_fingerprint.owner:
        print request.user
        print stored_fingerprint.owner
        return Response(data={'detail': "Only the owner of the fingerprint is allowed to modify it"}, status=403)
    if location_pk == -1:
        try:
            name = request.DATA['name']
            building_name = request.DATA['building_obj']['name']
        except Exception, e:
            log.error("Could not retrieve name and building name from this message:"+str(request.DATA))
            log.exception(e)
        try:
            location = Location.objects.get(name=name, building__name=building_name)
        except ObjectDoesNotExist:
            location = Location.objects.create(name=name, building__name=building_name, owner=request.user)
            location.save()
        location_pk = location.pk
    if stored_fingerprint.location_id == location_pk:
        stored_fingerprint.confirmed = True
        stored_fingerprint.save()
        changed = False
    else:
        stored_fingerprint.location = Location.objects.get(pk=location_pk)
        stored_fingerprint.confirmed = True
        stored_fingerprint.save()
        changed = True
        update_model(stored_fingerprint)
    response_data = {'changed': changed}
    log_task_end("Confirm location request")
    return Response(data=response_data)


def getCSV(request):
    if not 'building' in request.GET:
        return HttpResponse("Please specify a building, i.e. ?building=Building+Name")
    else:
        building_name = request.GET['building']
        filename = "/home/ubuntu/fingerprints_server/tracker_data/"+building_name+".model"
        try:
            f = open(filename)
            model = load(f)
            assert isinstance(model, ScikitModel)
            f.close()
            return HttpResponse(str(model.to_csv()))
        except Exception, e:
            return HttpResponse("Building not found: "+building_name+"\n"+str(e))


def getBuilding(msg):
    """
    :type msg: LocateMeMsg
    :param msg: Location msg
    :return: String building
    """
    if msg.building is None:
        return msg.building
    else:
        bssids = [scan.bssid for scan in msg.scans]
        scans_containing_bssid = Scan.objects.filter(base_station__bssid__in=bssids)
        possible_matching_fingerprint_ids = [scan.fingerprint for scan in scans_containing_bssid]
        possible_buildings = Fingerprint.objects.values_list('location__building',
                                                             pk__in=possible_matching_fingerprint_ids,
                                                             flat=True).distinct()
        if len(possible_buildings) == 1:
            return possible_buildings[0]
        elif len(possible_buildings) == 0:
            raise Exception("No building found")
        else:
            # deal with multiple possible buildings
            # for now, just warn and return the first.
            log.warn("Multiple buildings could match this query: " + str(possible_buildings))
            log.warn("Returning only the first.")
            return possible_buildings[0]


def getTracker(building_name):
    """
    Fails unless the tracker is in the cache.

    :type building_name: str
    :param building_name: The name of a building.
    :return: Returns a SciKit model that can predict locations on this building.
    :rtype: Tracker
    """
    try:
        filename = "/home/ubuntu/fingerprints_server/tracker_data/"+building_name+".tracker"
        last_modified = os.path.getmtime(filename)
        if cached_tracker and building_name in cached_tracker and cached_tracker['mod_date'] == last_modified:
            log.debug("Using current in-memory tracker")
            return cached_tracker[building_name]
        else:
            log.debug("Using pickled tracker")
            f = open(filename, 'rb')
            tracker = load(f)
            cached_tracker[building_name] = tracker
            cached_tracker['mod_date'] = last_modified
            f.close()
            return tracker
    except Exception, e:
        log.exception(e)
        if cached_tracker and building_name in cached_tracker:
            log.debug("Using old in-memory tracker")
            return cached_tracker[building_name]
        else:
            return None
