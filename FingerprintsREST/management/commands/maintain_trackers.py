from optparse import make_option
from time import sleep, time
from urllib import quote
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from lockfile import FileLock
import signal
from FingerprintsREST.models import Fingerprint, Building
from FingerprintsREST.views.MatchLocation.Learning import generateModel, Tracker
from logging import getLogger
from sys import getsizeof
from cPickle import dumps, dump, load
from os import path, mkdir, getpid
import daemon
from django.db import transaction

transaction.enter_transaction_management()


class Command(BaseCommand):
    args = 'building ...'
    help = """Maintains a tracking model for each building listed,
    by checking the database for new fingerprints at regular intervals.

    When the process finishes generating the model, it saves the machine learning function (not the data) to memcache
    for Django processes to access.

    When it sleeps, it pickles the data and saves it to a file to avoid taking up memory.

    To ensure a fast boot time, on initialization this process loads the model for each building consecutively,
    without sleeping in between. It also loads only a limited number of recent fingerprints, defaulting to 50.
    It sleeps once each model has been loaded.

    Each time the process wakes, it chooses the next building in the list to maintain - it does NOT update them all
    at once. This means that the memory overhead maximum is the size of the largest building, and that amount of memory
    will only be used every now and then, making this model highly memory efficient.

    Because updates are sent to the database first, there is no risk that data will be overriden in a race condition -
    all the data will make it into the database, and from there (eventually) into the trackers.

    To run without backgrounding the process, use the option --no-daemon

    The pid for the daemon created can be found in /var/run/maintain_trackers.pid (or you can set it using --pidfile.

    We use the configured Django log file instead of standard out if running in daemon mode.

    """
    option_list = BaseCommand.option_list + (
        make_option('--interval', '-i',
                    action='store',
                    dest='interval',
                    default=5,
                    help="""Sets the interval (in minutes) at which the database will be checked for new fingerprints.
                    Defaults to five minutes. Fractions of minutes are okay."""),
        make_option('--no-daemon',
                    dest='run_as_daemon',
                    action='store_false',
                    default=True,
                    help="""Instructs maintain_trackers to run in the foreground (useful for debugging). Log messages
                    will be printed to standard out or standard error, and no pid file will be created. Terminate with
                    Ctrl-C or equivalent"""),
        make_option('--data_dir',
                    dest='data_dir',
                    action='store',
                    default='tracker_data',
                    help="""This script will produce a file that temporarily stores data fr each building in the list.
                    Those files will be created in the given directory, with names as "<building_name>.pickle". Any
                     pre-existing files in the directory with the same name will be deleted.
                    If the path does not exist, it will be created. Relative or absolute pathnames are
                    acceptable."""),
        make_option('--pidfile', '--pid', '-p',
                    dest='pidfile',
                    action='store',
                    default='maintain_trackers.pid',
                    help="""Location of a file containing this processes pid. To terminate, run kill `cat <pidfile`"""),
        make_option('--lockfile', '--lock', '-l',
                    dest='lockfile',
                    action='store',
                    default='maintain_trackers.lock',
                    help="""Location of a file containing this processes lock.
                    This is supposed to prevent multiple simultaneous executions of this script."""),
        make_option('--initial_row_limit',
                    dest='initial_limit',
                    action='store',
                    default='5',
                    help="""To get running quickly, the initial models generated will only use a number of most recent
                    fingerprints per location set by this variable. Set 0 to indicate use all available."""),
        make_option('--long_term_row_limit',
                    dest='final_limit',
                    action='store',
                    default='25',
                    help="""Upon waking for the second time onwards, the models generated will use a number of most recent
                    fingerprints per location set by this variable. Set 0 to indicate use all available."""),
    )

    model = None
    logger = getLogger(__name__)

    def handle(self, *args, **options):
        self.is_daemon = False
        self.check_and_store_command_line_args(args, options)
        self.log("Will run as " + ("daemon" if self.run_as_daemon else "foreground thread") + " after initializing")
        try:
            self.initialize()
            self.startTime = time()
            if self.run_as_daemon:
                self.log("Entering daemon mode")
                self.is_daemon = True
                with self.daemonContext():
                    # self.logger = getLogger(__name__)
                    log = open("maintain_trackers.log", 'w')
                    log.write("Message\n")
                    log.close()
                    self.log("Message from the daemon")
                    pidfile = open(self.pidfile, 'w')
                    pidfile.write(str(getpid()))
                    pidfile.close()
                    self.log("pid = " + str(getpid()))
                    self.runForever()
            else:
                self.runForever()
        except Exception, e:
            import traceback

            self.err(traceback.format_exc())
            raise

    def daemonContext(self):
        return daemon.DaemonContext(pidfile=FileLock(self.lockfile),
                                    signal_map={
                                        signal.SIGUSR1: self.resetInterval,
                                        signal.SIGUSR2: self.updateAllImmediately,
                                    },
                                    working_directory=path.abspath("."),
                                    files_preserve=["/home/ubuntu/fingerprints_server/Django.log"],
                                    stdout=self.stdout,
                                    stderr=self.stderr)

    def check_and_store_command_line_args(self, args, options):
        # self.buildings - check that all buildings listed are actually in the database, or if the wildcard was used
        if len(args) > 0:
            self.buildings = args
            if len(self.buildings) == 1 and self.buildings[0] == ".":
                self.buildings = Building.objects.values_list('name', flat=True)
                self.log("Using all buildings: " + str(self.buildings))
            else:
                buildings_not_found = set(self.buildings).difference(
                    Building.objects.filter(name__in=self.buildings).values_list('name', flat=True))
                if len(buildings_not_found) > 0:
                    raise CommandError(
                        str(len(buildings_not_found)) + " buildings not found in the database. They were: " + str(
                            buildings_not_found) + ". Buildings in the database: " + str(
                            Building.objects.values_list('name', flat=True))
                    )
        else:
            raise CommandError(
                "No buildings specified. "
                "Please specify at least one building name as a command line argument. "
                "Use . to include all buildings")

        # self.run_as_daemon
        self.run_as_daemon = options['run_as_daemon']

        # self.data_dir - strip trailing slash, convert to an absolute file path if it's relative (and run_as_daemon is true) - create it if
        # necessary
        self.data_dir = path.abspath(options['data_dir'].rstrip("/"))
        if not path.exists(self.data_dir):
            self.log("Creating new directory for data storage: " + self.data_dir)
            mkdir(self.data_dir)

        # self.interval - convert to int, check is positive
        try:
            self.interval = int(options['interval'])
            if self.interval < 0:
                raise CommandError("interval must be a non-negative integer, but was " + str(self.interval))
        except Exception, cause:
            try:
                self.interval = float(options['interval'])
                if self.interval < 0:
                    raise CommandError("interval must be a non-negative integer, but was " + str(self.interval))
            except:
                raise CommandError("Invalid argument type for interval: must be int or float, not " +
                                   str(options['interval']) + ". Exception was: " + str(cause))

        # self.target_data_size - convert to int
        try:
            self.target_data_size = int(options['final_limit'])
        except Exception, cause:
            raise CommandError(
                "Invalid argument type for long_term_row_limit: must be int, not " + str(
                    type(options['final_limit'])) + ". Exception was: " + str(cause))

        # self.initial_limit - convert to int
        try:
            self.initial_limit = int(options['initial_limit'])
        except Exception, cause:
            raise CommandError(
                "Invalid argument type for initial_row_limit: must be int, not " + str(
                    type(options['initial_limit'])) + ". Exception was: " + str(cause))

        # self.pidfile & lockfile - only required if running as daemon, make absolute, check is valid file path
        if self.run_as_daemon:
            try:
                self.lockfile = path.abspath(options['lockfile'])
                self.pidfile = path.abspath(options['pidfile'])
            except Exception, cause:
                raise CommandError(
                    "Invalid argument to pidfile: should be a valid file path, but the following error was raised: " + str(
                        cause))

    def log(self, msg, ending="\n"):
        if self.is_daemon:
            self.logger.debug(str(msg))
        else:
            self.stdout.write(str(msg), ending=ending)
            self.logger.debug(str(msg))

    def err(self, msg, ending="\n"):
        if self.is_daemon:
            self.logger.error(str(msg))
        else:
            self.stderr.write(str(msg), ending=ending)
            self.logger.error(str(msg))

    def resetInterval(self):
        self.cur_interval = self.interval

    def updateAllImmediately(self):
        for _ in self.buildings:
            self.updateModelFromPickleAndDatabase()
            self.addTrackerToCache()
            self.nextBuilding()

    def initialize(self):
        self.firstBuilding()
        for _ in self.buildings:
            self.loadModelFromDatabase(self.initial_limit)
            self.addTrackerToCache()
            self.pickle()
            self.nextBuilding()
        for _ in self.buildings:
            self.loadModelFromDatabase(self.target_data_size)
            self.addTrackerToCache()
            self.pickle()
            self.nextBuilding()

    def runForever(self):
        while True:
            self.addTrackerToCache()
            self.pickle()
            self.sleep()
            self.startTime = time()
            self.nextBuilding()
            self.updateModelFromPickleAndDatabase()

    def firstBuilding(self):
        self.building_index = 0
        self.building = self.buildings[self.building_index]

    def nextBuilding(self):
        self.building = self.buildings[self.building_index]
        self.building_index += 1
        if self.building_index >= len(self.buildings):
            self.building_index = 0

    def loadModelFromDatabase(self, row_limit):
        '''
        Loads the most recent data from the database for the building, and then trains the model.
        '''
        self.log("Loading model for " + self.building + " from database")
        self.model = generateModel(self.building, row_limit)
        self.log("Finished loading " + self.building + " from database")

    # We're going to ignore the actual cache for now due to the high prevalence of cache errors.
    # Instead, load from pickled files then keep in process memory.
    def addTrackerToCache(self):
        self.log("Pickling tracker for " + self.building + " to " + self.data_dir + "/" + self.building + ".tracker")
        with open(self.data_dir + "/" + self.building + ".tracker", 'wb') as picklefile:
            dump(Tracker(self.model), picklefile, protocol=2)

            # cache.set(quote(self.building), Tracker(self.model))
            # if cache.get(quote(self.building)) is None:
            #     self.err("Unable to add tracker to cache - cache may be full. "
            #              "\nSize of tracker was " + str(getsizeof(dumps(Tracker(self.model)))) +
            #              "\nSize of model was " + str(getsizeof(dumps(self.model))))
            # else:
            #     self.log("Successfully added tracker for " + quote(self.building) + " to the cache"
            #              "\nSize of tracker was " + str(getsizeof(dumps(Tracker(self.model)))) +
            #              "\nSize of model was " + str(getsizeof(dumps(self.model))))

    def updateModelFromPickleAndDatabase(self):
        self.unpickle()
        self.log("Getting fingerprints more recent than " + str(self.model.last_updated))
        transaction.commit()  # Whenever you want to see new data
        # self.log("Query == Fingerprint.objects.filter(timestamp__gt=\""+str(self.model.last_updated)+"\", location__building__name=\""+str(self.building)+"\", confirmed=True)")
        new_fingerprints = Fingerprint.objects.filter(timestamp__gt=str(self.model.last_updated),
                                                      location__building__name=str(self.building), confirmed=True) \
            .order_by('-timestamp')
        print new_fingerprints
        for fingerprint in new_fingerprints:
            self.model.add_fingerprint(fingerprint)
            # code to overwrite old data points with new ones once the limit is reached
            # is implemented within add_fingerprint

        self.log("Finished updating model with " + str(len(new_fingerprints)) + " new fingerprints")

    def sleep(self):
        try:
            self.cur_interval
        except AttributeError:
            self.cur_interval = self.interval
        sleepUntil = self.startTime + self.cur_interval * 60
        if time() < sleepUntil:
            self.log("Will sleep for " + str(sleepUntil - time()) + " seconds")
            sleep(sleepUntil - time())
        else:
            self.err(
                "Unable to execute task within interval - now doubling interval from " + str(self.cur_interval))
            self.cur_interval *= 2
            self.err("To " + str(self.cur_interval) + " minutes")
            self.sleep()  # loop until the interval is big enough
            self.log("Waking up...")

    def pickle(self):
        self.log("Pickling model for " + self.building + " to " + self.data_dir + "/" + self.building + ".model")
        with open(self.data_dir + "/" + self.building + ".model", 'wb') as picklefile:
            dump(self.model, picklefile, protocol=2)

    def unpickle(self):
        self.log("Unpickling model for " + self.building + " from " + self.data_dir + "/" + self.building + ".model")
        with open(self.data_dir + "/" + self.building + ".model", 'rb') as picklefile:
            self.model = load(picklefile)


