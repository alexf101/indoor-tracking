from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from FingerprintsREST.permissions import IsOwnerOrReadOnly
import logging
from FingerprintsREST.views.CustomViewSets import QueryableViewSet

log = logging.getLogger(__name__)


class OwnedViewSerializer(serializers.HyperlinkedModelSerializer):
    # id = serializers.Field()
    owner = serializers.Field(source='owner.username')


class OwnedViewSet(QueryableViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)

    def pre_save(self, obj):
        if self.request.user.is_authenticated():
            log.debug(obj)
            print "OwnedViewSet pre-save"
            obj.owner = self.request.user
