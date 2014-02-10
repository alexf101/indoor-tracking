from django.db import models
from Fingerprint import Fingerprint


class MagneticField(models.Model):
    direction = models.FloatField()
    magnitude = models.FloatField()
    zaxis = models.FloatField()
    fingerprint = models.ForeignKey(Fingerprint)

    class Meta:
        app_label = "FingerprintsREST"