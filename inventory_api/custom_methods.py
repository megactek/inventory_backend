from rest_framework.permissions import BasePermission
from .utils import decode_jwt
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response


class IsAuthenticatedCustom(BasePermission):
    def has_permission(self, request, _):
        auth_token = request.META.get("HTTP_AUTHORIZATION", None)

        if not auth_token:
            return False

        user = decode_jwt(auth_token)

        if not user:
            return False

        request.user = user

        return True


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    exc_list = str(exc).split("DETAIL: ")
    return Response({"error": exc_list[-1]}, status=status.HTTP_403_FORBIDDEN)
