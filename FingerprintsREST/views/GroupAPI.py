from django.contrib.auth.models import Group
from OwnedViews import OwnedViewSet, OwnedViewSerializer


class GroupViewSerializer(OwnedViewSerializer):
    class Meta:
        model = Group


class GroupViewSet(OwnedViewSet):
    """
    The idea of groups is to create a sub-community, managed by the group creator.

    You can create groups here, and users can join groups using the users api.

    If a user is a member of a group that you own, you can modify the data that they submit. Effectively, you gain
    admin powers over their accounts.

    The intention is that this can be used to allow you to moderate your own community of users.

    You can also use this to see only fingerprints submitted by the groups you are a member of.

    PLEASE NOTE THAT THE ABOVE FUNCTIONALITY IS UNDER DISCUSSION BUT HAS NOT BEEN IMPLEMENTED YET.
    """
    queryset = Group.objects.all()
    serializer_class = GroupViewSerializer