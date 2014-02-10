from django.test import TestCase
import datetime
import json
from FingerprintsREST.tests.commons import *


class LocationRetrievalTests(TestCase):
    def setUp(self):
        setUpDefaultDatabaseAndClearCache()

    def testSetUp(self):
        pass

    def testGetLocation(self):
        locations = postGetLocation()
        expected_location = {
            "fingerprint_id": 4,
            "locations": [
                {
                    "owner": "test_user",
                    "id": 1,
                    "url": "http://testserver/api/locations/1",
                    "name": "test_location",
                    "description": "",
                    "building": "http://testserver/api/buildings/1"
                }
            ]
        }
        # API may grow to include more than the expected keys/values, but should contain at least these pairs.
        assert is_dictionary_subset(expected_location, locations)
        self.new_fingerprint_pk = locations['fingerprint_id']
        self.location_found = locations['locations'][0]['name']
        self.location_found_pk = locations['locations'][0]['url'][-1]
        assert self.location_found == "test_location"

    def testConfirmLocation(self):
        self.testGetLocation()
        url = "confirm/%s/%s" % (self.location_found_pk, self.new_fingerprint_pk)
        print url
        result = put(url)
        assert result["changed"] is True



