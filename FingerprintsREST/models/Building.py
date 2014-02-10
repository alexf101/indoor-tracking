from django.db import models

from django.contrib.auth.models import User
#from defaults import DEFAULT_MAX_TEXT_LENGTH


class Building(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    owner = models.ForeignKey(User)

    class Meta:
        app_label = "FingerprintsREST"

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name