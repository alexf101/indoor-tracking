from django.db import models
from FingerprintsREST.models import BaseStation, Fingerprint


class Scan(models.Model):
    level = models.IntegerField()
    base_station = models.ForeignKey(BaseStation)
    fingerprint = models.ForeignKey(Fingerprint, related_name='scans')

    class Meta:
        app_label = "FingerprintsREST"

    def keys(self):
        return [self.level, self.base_station, self.fingerprint]

    def __str__(self):
        return ", ".join(map(str, self.keys()))

    def __unicode__(self):
        return str(self)