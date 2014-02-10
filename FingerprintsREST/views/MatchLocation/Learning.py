from datetime import datetime
import logging, time
from django.utils import timezone
from FingerprintsREST.models import Fingerprint, Location, Device
from predictors import predictor
from FingerprintsREST.utils import log_task_start, log_task_end
from collections import Counter


log = logging.getLogger(__name__)

NON_SCAN_PARAMETERS = 3  # orientation, magnitude, zaxis


def getDeviceCalibrationConstants():
    '''
    TODO this method returns a manually calculated list of calibration constants.
    It should be dynamically generated based on the data!!!

    See the following snippets for a start on how to set this up:

    from collections import defaultdict

    def average_loc_ap(device):
        dfps = fps.filter(device=device)
        fpat = defaultdict(list)
        for f in dfps:
            fpat[f.location].append(f)
        print "DONE GETTING FINGERPRINTS AT LOCATIONS"
        mean_device_location_ap = {}
        for location in locations:
            visible_aps = defaultdict(list)
            for fp in fpat[location]:
                for scan in fp.scans.all():
                    visible_aps[scan.base_station].append(scan.level)
            for ap, results in visible_aps.iteritems():
                mean_device_location_ap[(location, ap)] = mean(results)
        return mean_device_location_ap

    def mean_diff(d1, d2):
        d1_loc_ap = device_map[d1]
        d2_loc_ap = device_map[d2]
        differences = []
        mismatches = 0
        for locap, average in d2_loc_ap.iteritems():
            try:
                differences.append(d1_loc_ap[locap] - average)
            except:
                mismatches += 1
        if len(differences) > 1:
            result = sqrt(var(differences))
        else:
            result = nan
        return result, len(d2_loc_ap) - mismatches

    from itertools import combinations
    #print "some random examples", array(differences)[random.randint(0, len(differences)-1, 30)]
    for d1, d2 in combinations(devices, 2):
        sdev, matches = mean_diff(d1, d2)
        serr = sdev / sqrt(matches)
        print d1, "-", d2, "=", serr, "with", matches, "matches"
    '''
    # everything is relative to the Huawei G300. i.e. the relevant value should be added to any phone
    # that isn't the Huawei G300 to predict what a Huawei G300 would've seen.
    return {
        Device.objects.get(name='GT-I9100'): -4.92,
        Device.objects.get(name='HTC_PN071'): -6.79,
        Device.objects.get(name='Nexus 4'): -4.86,
        Device.objects.get(name='U8815'): 0,
    }


def generateModel(building_name, row_limit_per_location=25):
    """

    :param building_name: Name of building
    :rtype: ScikitModel
    :return: Machine learning model matching building
    """
    log_task_start("Generating model")
    column_names, rows, classes, rooms, null_value, most_recent = generateData(building_name, row_limit_per_location)
    model = ScikitModel(rows, classes, rooms, column_names, null_value, row_limit_per_location, most_recent)
    log_task_end("Generating model")
    return model


def generateData(building_name, row_limit_per_location=25):
    log_task_start("Getting fingerprints from database")
    if row_limit_per_location > 0:
        locations = Location.objects.filter(building__name=building_name)
        matchingFingerprints = []
        for location in locations:
            # take only the most recent n fingerprints at each location
            fingerprintsAtLocation = \
                Fingerprint.objects.filter(location=location, confirmed=True) \
                    .order_by("-timestamp")[:row_limit_per_location]
            matchingFingerprints += fingerprintsAtLocation
    else:
        matchingFingerprints = \
            Fingerprint.objects.filter(location__building__name=building_name, confirmed=True)  # take all fingerprints
    column_names = _get_all_base_stations(matchingFingerprints)
    log_task_end("Getting fingerprints from database")
    log_task_start("Parsing into rows")
    rows, classes, rooms, null_value, most_recent = _to_rows(column_names, matchingFingerprints)
    log_task_end("Parsing into rows")
    return column_names, rows, classes, rooms, null_value, most_recent


def fingerprintsToModel(matchingFingerprints, row_limit_per_location=25):
    column_names = _get_all_base_stations(matchingFingerprints)
    rows, classes, rooms, null_value, most_recent = _to_rows(column_names, matchingFingerprints)
    model = ScikitModel(rows, classes, rooms, column_names, null_value, row_limit_per_location, most_recent)
    return model


def _get_all_base_stations(fingerprints):
    '''
    Gets the unique set of base stations in the input data, and assigns to each of them an index to use for columns.
    :param fingerprints: list of fingerprints
    :return: A dictionary of {base_station.pk -> integer_index}
    '''
    matchingScans = _get_all_scans(fingerprints)
    unique_base_stations = set([scan.base_station.pk for scan in matchingScans])
    return dict([(y, x) for (x, y) in enumerate(unique_base_stations)])


def _get_all_scans(fingerprints):
    """
    :type fingerprints: [Fingerprint]
    :param fingerprints: List of Fingerprints
    :return: All scans in the fingerprints as a flat list
    :rtype: [Scan]
    """
    matchingScans = []
    for fingerprint in fingerprints:
        for scan in fingerprint.scans.all():
            matchingScans.append(scan)
    return matchingScans


def _to_rows(column_names, matchingFingerprints):
    """
    Returns a 2D list of data.

    There is no header.

    The first columns will be set based on scans, the final column based on location (i.e. class), the rest based on
    the magnetic parameters of the fingerprint.

    :type column_names: dict
    :param column_names:
    :type matchingFingerprints: [Fingerprint]
    :param matchingFingerprints:
    :return: A list containing rows of data, and a list of classes, one entry sfor each row.
    """

    deviceOffsetMap = getDeviceCalibrationConstants()

    null_value = -500  # all other values should be negative
    if len(matchingFingerprints) > 0:
        most_recent = matchingFingerprints[0].timestamp
    min_so_far = null_value
    data = []
    classes = []
    rooms = []
    for fingerprint in matchingFingerprints:
        if fingerprint.timestamp > most_recent:
            most_recent = fingerprint.timestamp
        deviceOffset = deviceOffsetMap[fingerprint.device]
        row, scan_min = _to_row(column_names, null_value, fingerprint, deviceOffset)
        min_so_far = scan_min if scan_min < min_so_far else min_so_far
        data.append(row)
        classes.append(fingerprint.location.pk)
        rooms.append(fingerprint.location.room)
    #min_so_far -= 1
    #for row in data:
    #    for index, value in enumerate(row[:-NON_SCAN_PARAMETERS]):
    #        if value == null_value:
    #            row[index] = min_so_far
    # TODO our algorithm isn't using the imputed null_value, so let's mark nulls arbitrarily and simply report this value
    # The above makes it more convenient to deal with device heterogeneity by just ignoring the likely threshold
    return data, classes, rooms, null_value, most_recent


def _to_row(column_names, null_value, fingerprint, deviceOffset):
    """Converts a fingerprint to a data row, assuming the column names have indexes for all the base stations in the
    fingerprint.
    :param column_names: dictionary of base_station.pk to column indexes
    :param null_value: value to use for when the fingerprint doesn't detect a base station
    :param fingerprint: fingerprint
    :return: The row vector, and the minimum scan level seen.
    """
    row = [null_value] * len(column_names)
    scan_min = 0
    for scan in fingerprint.scans.all():
        adjustedLevel = scan.level + deviceOffset
        scan_min = adjustedLevel if adjustedLevel < scan_min else scan_min
        try:
            row[column_names[scan.base_station.pk]] = adjustedLevel
        except KeyError:
            log.debug("Unrecognised base station: " + str(scan.base_station))
    row.append(fingerprint.direction)
    row.append(fingerprint.magnitude)
    row.append(fingerprint.zaxis)
    return row, scan_min


class Tracker():
    def __init__(self, model):
        self.predictor = model.predictor
        self.column_names = model.column_names
        self.null_value = model.null_value

    def guess(self, fingerprint):
        '''
        :rtype: int
        :param fingerprint:
        :return: location_id
        '''
        vector, _ = _to_row(self.column_names, self.null_value, fingerprint)
        return self.predictor.predict(vector)[0]

    def guess_all(self, fingerprint):
        '''28:40
        :rtype {}
        :param fingerprint:
        :return: location id's ordered by probability
        '''
        vector, _ = _to_row(self.column_names, self.null_value, fingerprint)
        prediction = self.predictor.predict(vector)
        return prediction


class ScikitModel():
    # the row which contains the least recent fingerprint - on reaching the data limit,
    # the model will overwrite itself in a loop so that the oldest value is overwritten by the newest.

    def __init__(self, data, classes, rooms, column_names, null_value, row_limit_per_location,
                 most_recent=timezone.make_aware(datetime.fromtimestamp(0), timezone.get_default_timezone())):
        """
        data should be added initially in order of timestamp, but is not guaranteed to remain so
        :type data: [[]]
        :type classes: []
        :type column_names: dict
        :param data:
        :param classes:
        :param column_names:
        """
        self.data = data
        self.classes = classes
        self.rooms = rooms
        self.column_names = column_names
        self.null_value = null_value
        self.row_limit_per_location = row_limit_per_location
        self.setPredictor()
        self.train()
        self.location_counts = Counter(classes)  # count of each location pk
        # rownum of oldest fingerprint at each location pk: [pk] = oldest_rownum
        self.oldest_fingerprints = self.initOldestFingerprints()
        self.last_updated = most_recent

    def initOldestFingerprints(self):
        oldest_fingerprints = {}
        for rownum, location in enumerate(self.classes):
            if not location in oldest_fingerprints:
                oldest_fingerprints[location] = rownum
        return oldest_fingerprints

    def setPredictor(self):
        self.predictor = predictor(self.null_value)

    def train(self):
        self.predictor.fit(self.data, self.classes)

    def add_fingerprint(self, fingerprint):
        self.last_updated = fingerprint.timestamp
        # check for input errors
        log_task_start("Adding fingerprint")
        assert fingerprint.confirmed and fingerprint.location is not None
        # check for new base station
        self.update_if_new_base_stations(fingerprint)
        # append new row (don't forget to append to both DATA and CLASSES)
        vector, scan_min = _to_row(self.column_names, self.null_value, fingerprint)
        # check if we can append this fingerprint, or have to replace an existing old one
        if self.location_counts[fingerprint.location.pk] < self.row_limit_per_location:
            log.debug("Appending new row as existing location count, " + str(
                self.location_counts[fingerprint.location.pk]) + ", is less than limit, " + str(
                self.row_limit_per_location))
            self.data.append(vector)
            self.classes.append(fingerprint.location.pk)
            # keep counter of fingerprints at this fingerprint's location up to date
            self.location_counts[fingerprint.location.pk] += 1
        else:
            log.debug("Replaced old row with new, and updated old as existing location count, " + str(
                self.location_counts[fingerprint.location.pk]) + ", is greater than limit, " + str(
                self.row_limit_per_location))
            oldrow = self.oldest_fingerprints[fingerprint.location.pk]
            log.debug("Rownum replaced: " + str(oldrow))
            self.data[oldrow] = vector
            assert self.classes[oldrow] == fingerprint.location.pk
            # linear search for the next oldest instance
            oldrow += 1
            while self.classes[oldrow] != fingerprint.location.pk:
                oldrow += 1
                if oldrow == len(self.classes):
                    oldrow = 0
                    # oldrow now points to the next instance of the fingerprint location
            self.oldest_fingerprints[fingerprint.location.pk] = oldrow
            # check for new weakest signal
        self.update_if_weakest_signal(scan_min)
        log_task_start("Retraining model on updated data")
        log.debug(str(len(self.data)) + " rows")
        self.train()
        log_task_end("Retraining model on updated data")
        log_task_end("Adding fingerprint")

    def update_if_new_base_stations(self, fingerprint):
        new_column_names = filter(lambda column_name: column_name not in self.column_names,
                                  _get_all_base_stations([fingerprint]))
        if len(new_column_names) > 0:
            log.debug("New columns found")
            log.debug("Old columns: " + str(self.column_names))
            log.debug("New columns: " + str(new_column_names))
            # get the indexes for the new columns
            i = len(self.data[0]) - NON_SCAN_PARAMETERS
            for new_column_name in new_column_names:
                self.column_names[new_column_name] = i
                i += 1
                # add null values for that data
            for row in self.data:
                for _ in new_column_names:
                    row.insert(len(row) - NON_SCAN_PARAMETERS, self.null_value)
            log.debug("Merge result: " + str(self.column_names))

    def update_if_weakest_signal(self, weakest_signal_in_fingerprint):
        if weakest_signal_in_fingerprint <= self.null_value:
            log.debug("New minimum value found: " + str(weakest_signal_in_fingerprint))
            log.debug("Old null value: " + str(self.null_value))
            new_null_value = weakest_signal_in_fingerprint - 1
            for row in self.data:
                for index, value in enumerate(row):
                    if value == self.null_value:
                        row[index] = new_null_value
            self.null_value = new_null_value
            log.debug("New null value: " + str(self.null_value))

    def to_csv(self):
        header = ",".join(
            map(lambda x: '"' + str(x[0]) + '"',
                sorted(self.column_names.items(), key=lambda x: x[1])
            )
        ) + ',"orientation","magnitude","zaxis","location_id","room"'
        body = "\n".join(
            [",".join(
                [str(val) for val in row]) + "," + str(clas) + "," + '"' + str(room) + '"'
             for row, clas, room in zip(self.data, self.classes, self.rooms)])
        return header + "\n" + body

    # returns as a CSV
    def __str__(self):
        return self.to_csv()

    def __eq__(self, other):
        return self.data == other.data and self.classes == other.classes
