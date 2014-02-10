from django.db import models
from django.contrib.auth.models import User


class Device(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)
    version = models.CharField(max_length=32, blank=True)
    manufacturer = models.CharField(max_length=32, blank=True)

    class Meta:
        app_label = "FingerprintsREST"

    def __str__(self):
        return self.name + " " + self.version

    def __unicode__(self):
        return self.name + " " + self.version