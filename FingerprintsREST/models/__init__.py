from Building import Building
from Device import Device
from Location import Location
from BaseStation import BaseStation
from Fingerprint import Fingerprint
from Scan import Scan

from django.contrib import admin

admin.site.register(Building)
admin.site.register(Device)
admin.site.register(Location)
admin.site.register(BaseStation)
admin.site.register(Fingerprint)
admin.site.register(Scan)