from django.contrib.auth.models import User
from django.db import models
from defaults import DEFAULT_MAX_TEXT_LENGTH


class BaseStation(models.Model):
    bssid = models.CharField(db_index=True, max_length=DEFAULT_MAX_TEXT_LENGTH)
    ssid = models.CharField(max_length=DEFAULT_MAX_TEXT_LENGTH)
    frequency = models.IntegerField()
    manufacturer = models.CharField(max_length=32, blank=True)
    model = models.CharField(max_length=32, blank=True)
    owner = models.ForeignKey(User)  # use a list of owners? Thought of more as subscribers?

    class Meta:
        app_label = "FingerprintsREST"
        unique_together = (("bssid", "frequency"),)

    def keys(self):
        return self.bssid, self.ssid, self.frequency

    def __str__(self):
        return ", ".join(map(str, self.keys()))

    def __unicode__(self):
        return str(self)
