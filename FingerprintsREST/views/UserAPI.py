from django.contrib.auth.models import User
from rest_framework import viewsets, serializers, generics, permissions as rest_permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.response import Response
from FingerprintsREST.permissions import IsOwner
from FingerprintsREST.views.CustomViewSets import filter_query_set


class basic_user_serializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ['url', 'email', 'username']


class create_user_serializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def save_object(self, obj, **kwargs):
        if obj.pk is None:
            print "Creating new user: "+str(obj)
            User.objects.create_user(obj.username, obj.email, obj.password)
        else:
            print "Updating existing user: "+str(obj)
            stored_password = User.objects.get(pk=obj.pk).password
            if obj.password != stored_password:
                print "Password change detected"
                obj.set_password(obj.password)
            obj.save()


class CreateOrList(generics.GenericAPIView):
    """
    List all users, or create a new one.
    """
    authentication_classes = []
    serializer_class = create_user_serializer

    # noinspection PyUnusedLocal,PyShadowingBuiltins
    def get(self, request, format=None):

        users = User.objects.all()

        query, is_dictionary = filter_query_set(request, users)
        if is_dictionary:
            return Response(query)
        else:
            serializer = basic_user_serializer(query, context={'request': request}, many=True)
            return Response(serializer.data)

    # noinspection PyUnusedLocal,PyShadowingBuiltins
    def post(self, request, format=None):
        serializer = create_user_serializer(data=request.DATA, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#
# class Create(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = create_user_serializer
#
#     #def save(self, obj):
#     #    User.objects.create_user(obj.username, obj.email, obj.password)


class RetrieveUpdateOrDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = create_user_serializer
    permission_classes = (IsAuthenticated, IsOwner)


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Administrators only!

    Create new admin users, or edit/delete other users.
    """
    model = User
    queryset = User.objects.all()
    permission_classes = (rest_permissions.IsAuthenticated, rest_permissions.IsAdminUser)
