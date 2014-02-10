from django.db import models

from django.contrib.auth.models import User
from FingerprintsREST.models import Building
from defaults import DEFAULT_MAX_TEXT_LENGTH


class Location(models.Model):
    name = models.CharField(max_length=DEFAULT_MAX_TEXT_LENGTH)
    description = models.CharField(max_length=DEFAULT_MAX_TEXT_LENGTH, blank=True, default="")
    room = models.CharField(max_length=DEFAULT_MAX_TEXT_LENGTH, blank=True, default="")
    building = models.ForeignKey(Building)
    owner = models.ForeignKey(User)

    class Meta:
        app_label = "FingerprintsREST"
        unique_together = (('name', 'building'),)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name