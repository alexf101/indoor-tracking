from django.test.client import Client
import logging
import json
import datetime
from django.core.cache import cache

log = logging.getLogger(__name__)
client = Client()


def is_dictionary_subset(subdic, superdic):
    '''
    >>> d1 = {"apple": 1, "banana": "fruit", "pineapple": ["green", "spiky"]}
    >>> d2 = dict(d1.items())
    >>> is_dictionary_subset(d1, d2)
    True
    >>> is_dictionary_subset(d2, d1)
    True
    >>> d1["mango"] = "delicious"
    >>> is_dictionary_subset(d1, d2)
    False
    >>> is_dictionary_subset(d2, d1)
    True

    Tests for subset (keys & values) relationship between two dictionaries.

    May fail if values of either dictionary are not hashable.
    :param subdic:
    :type subdic: dict
    :param superdic:
    :type superdic: dict
    :return: True if subdic is a subset (both keys & values) of superdic, False otherwise
    '''
    return_val = True
    for key, value in subdic.iteritems():
        return_val &= key in superdic and superdic[key] == value
    return return_val


def curTime(future_secs=0):
    return (datetime.datetime.now() + datetime.timedelta(0, future_secs)).strftime("%Y-%m-%d %H:%M:%S")


def setUpDefaultDatabaseAndClearCache():
    cache.clear()
    postUser()
    login()
    postBuilding()
    postLocation()
    postLocation(location_name="test_location_2")
    postFingerprint()
    postFingerprint(timestamp=curTime(1))
    postFingerprint(scans=[
        {
            "base_station": {
                'bssid': "BSSID_OF_TEST_BASE_STATION_1",
                'ssid': "SSID_OF_TEST_NETWORK_1",
                'frequency': 2246,
            },
            'level': -80
        },
        {
            "base_station": {
                'bssid': "BSSID_OF_TEST_BASE_STATION_2",
                'ssid': "SSID_OF_TEST_NETWORK_1",
                'frequency': 2246,
            },
            'level': -55
        },
        {
            "base_station": {# belongs to the neighbour - barely visible!
                             'bssid': "BSSID_OF_TEST_BASE_STATION_X",
                             'ssid': "SSID_OF_TEST_NETWORK_X",
                             'frequency': 3387,
            },
            'level': -99
        },
    ], location_url="http://testserver/api/locations/2/")


def wrap(s):
    return "/api/" + s + "/"


def post(url, data, uname='test_user', pwd='test_password'):
    return send(client.post, url, data=data, uname=uname, pwd=pwd)


def put(url, data, uname='test_user', pwd='test_password'):
    return send(client.put, url, data=data, uname=uname, pwd=pwd)


def put(url, uname='test_user', pwd='test_password'):
    return send(client.put, url, uname, pwd)


def send(method, url, data=None, uname='test_user', pwd='test_password'):
    if data is not None:
        response = method(wrap(url), data=data, auth=(uname, pwd), content_type='application/json')
    else:
        response = method(wrap(url), auth=(uname, pwd), content_type='application/json')
    print response
    return json.loads(response.content)


def login():
    client.login(username='test_user', password='test_password')


def post_noauth(url, data):
    response = client.post(wrap(url), data=data, content_type='application/json')
    print response
    return json.loads(response.content)


def postUser(email="test@email.net", username="test_user", password="test_password"):
    user = {
        'email': email,
        'username': username,
        'password': password
    }
    return post_noauth('users', data=json.dumps(user))


def postBuilding(building_name="Ian Potter Museum"):
    building = {
        'name': building_name
    }
    return post('buildings', data=json.dumps(building))


def postLocation(building_url="http://testserver/api/buildings/1/", location_name="test_location"):
    location = {
        'name': location_name,
        'building': building_url
    }
    return post('locations', data=json.dumps(location))


def defaultScans():
    return [
        {
            "base_station": {
                'bssid': "BSSID_OF_TEST_BASE_STATION_1",
                'ssid': "SSID_OF_TEST_NETWORK_1",
                'frequency': 2246,
            },
            'level': -67
        },
        {
            "base_station": {
                'bssid': "BSSID_OF_TEST_BASE_STATION_2",
                'ssid': "SSID_OF_TEST_NETWORK_1",
                'frequency': 2246,
            },
            'level': -78
        },
        {
            "base_station": {
                'bssid': "BSSID_OF_TEST_BASE_STATION_3",
                'ssid': "SSID_OF_TEST_NETWORK_1",
                'frequency': 3387,
            },
            'level': -90
        },
    ]


def postFingerprint(scans=defaultScans(),
                    location_url="http://testserver/api/locations/1/",
                    timestamp=curTime(),
                    zaxis=18,
                    magnitude=22,
                    direction=266):
    fingerprint = {
        'scans': scans,
        'location': location_url,
        'timestamp': timestamp,
        'zaxis': zaxis,
        'magnitude': magnitude,
        'direction': direction,
    }
    return post('fingerprints', data=json.dumps(fingerprint))


def postGetLocation(scans=defaultScans()):
    msg = {
        'fingerprint':
            {
                'scans': scans,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'zaxis': 18,
                'magnitude': 22,
                'direction': 266,
            },
        'building': "Ian Potter Museum",
    }
    return post("mylocation", json.dumps(msg))