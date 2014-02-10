# Test that the model data looks correct after adding new fingerprints.

# Check that the null_values update properly.

# Check that only 1000 fingerprints are used...

# Test device scalings
import urllib
from django.test import TestCase
from FingerprintsREST.tests.commons import *
from FingerprintsREST.views.MatchLocation.Learning import ScikitModel
from django.core.cache import cache


class ModelTests(TestCase):
    def setUp(self):
        setUpDefaultDatabaseAndClearCache()

    def testCache(self):
        cache.set("banana", "fruit")
        assert cache.get("banana") is not None
        assert cache.get("banana") == "fruit"

    def testRetrieveModelFromCache(self):
        model_before = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertIsNone(model_before)
        postGetLocation()
        model_after = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertIsNotNone(model_after)
        self.assertIsInstance(model_after, ScikitModel)
        # this shows that the null_value's are updating properly: it will only become -100 after the -99
        # in the second row
        self.assertEqual(model_after.data, [
            [-67, -78, -90, -100, 266.0, 22.0, 18.0],
            [-67, -78, -90, -100, 266.0, 22.0, 18.0],
            [-80, -55, -100, -99, 266.0, 22.0, 18.0],
        ])

    def testAddNewFingerprints(self):
        new_fingerprint_id = postGetLocation()["fingerprint_id"]
        model_before = cache.get(urllib.quote("Ian Potter Museum"))
        assert put("confirm/1/" + str(new_fingerprint_id))["changed"] is True
        model_after = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertNotEqual(model_before.data, model_after.data)
        self.assertEqual(len(model_before.data), 3)
        self.assertEqual(len(model_after.data), 4)

    def testNewNullValue(self):
        scans = defaultScans()
        scans[0]['level'] = -103
        postGetLocation()
        model_before = cache.get(urllib.quote("Ian Potter Museum"))
        nfid = postGetLocation(scans)["fingerprint_id"]
        model_after = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertEqual(model_before, model_after)  # no difference until confirm
        put("confirm/1/" + str(nfid))
        model_after = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertNotEqual(model_before, model_after)
        self.assertEqual(model_after.data, [
            [-67, -78, -90, -104, 266.0, 22.0, 18.0],
            [-67, -78, -90, -104, 266.0, 22.0, 18.0],
            [-80, -55, -104, -99, 266.0, 22.0, 18.0],
            [-103, -78, -90, -104, 266.0, 22.0, 18.0]])
        self.assertEqual(model_after.classes, [1,1,2,1])

    def testNewBaseStation(self):
        scans = defaultScans()
        scans[0]['base_station']['bssid'] = "new_test_base_station"
        postGetLocation()
        model_before = cache.get(urllib.quote("Ian Potter Museum"))
        nfid = postGetLocation(scans)["fingerprint_id"]
        model_after = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertEqual(model_before, model_after)  # no difference until confirm
        put("confirm/2/" + str(nfid))
        model_after = cache.get(urllib.quote("Ian Potter Museum"))
        self.assertNotEqual(model_before, model_after)
        #print str(model_after)
        print model_after.data
        self.assertItemsEqual(model_after.data, [
            [-67, -78, -90, -100, -100, 266.0, 22.0, 18.0],
            [-80, -55, -100, -99, -100, 266.0, 22.0, 18.0],
            [-67, -78, -90, -100, -100, 266.0, 22.0, 18.0],
            [-100, -78, -90, -100, -67, 266.0, 22.0, 18.0]])
        self.assertItemsEqual(model_after.classes, [1,2,1,2])