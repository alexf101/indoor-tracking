from django.db import models

from django.contrib.auth.models import User
from FingerprintsREST.models import Location, Device


class Fingerprint(models.Model):
    location = models.ForeignKey(Location, blank=True, default=None)
    timestamp = models.DateTimeField()
    device = models.ForeignKey(Device, blank=True, default=None)
    owner = models.ForeignKey(User)
    direction = models.FloatField()
    magnitude = models.FloatField()
    zaxis = models.FloatField()
    confirmed = models.BooleanField(default=False)
    #scans = reverse foreign key [scans]

    class Meta:
        app_label = "FingerprintsREST"

    def keys(self):
        try:
            return (self.location, self.confirmed, self.timestamp, self.owner, self.direction,
                self.magnitude, self.zaxis)
        except:
            return (self.timestamp, self.owner, self.direction, self.magnitude, self.zaxis)

    def __str__(self):
        return ", ".join(map(str, self.keys()))

    def __unicode__(self):
        return str(self)