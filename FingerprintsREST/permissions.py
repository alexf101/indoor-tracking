from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object level permission to only allow owners of an object to edit it.

    Be sure to call IsAuthenticatedOrReadOnly first.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object, or if the object IS the user
        return obj == request.user or obj.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Object level permission to only allow owners of an object to view or edit it.

    Be sure to call IsAuthenticated first.
    """
    def has_object_permission(self, request, view, obj):
        # noinspection PyBroadException
        try:
            return obj == request.user or obj.owner == request.user
        except:
            return False