from inventory_api.custom_methods import IsAuthenticatedCustom
from inventory_api.utils import get_access_token, CustomPagination, get_query
from .serializer import (
    CreateUserSerializer,
    CustomUser,
    CustomUserSerializer,
    LoginSerializer,
    UpdatePasswordSerializer,
    UserActivitySerializer,
    UserActivities,
)
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import status
from datetime import datetime


def add_user_Activity(user, action):
    UserActivities.objects.create(
        user_id=user.id, email=user.email, fullname=user.fullname, action=action
    )


class CreateUserView(ModelViewSet):
    http_method_names = ["post"]
    queryset = CustomUser.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = (IsAuthenticatedCustom,)

    def create(self, request, *args, **kwargs):

        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)

        CustomUser.objects.create(**valid_request.validated_data)
        add_user_Activity(request.user, "added new user")
        return Response({"success": "User Created"}, status=status.HTTP_201_CREATED)


class LoginView(ModelViewSet):
    queryset = CreateUserView.queryset
    serializer_class = LoginSerializer
    http_method_names = ["post"]

    def create(self, request):
        valid_request = self.serializer_class(data=request.data)
        valid_request.is_valid(raise_exception=True)

        new_user = valid_request.validated_data.get("is_new_user")

        if new_user:
            user = CustomUser.objects.filter(
                email=valid_request.validated_data["email"]
            )
            if user:
                user = user[0]

                if not user.password:
                    return Response({"user_id": str(user.id)})
                else:
                    raise Exception("User Password has been set")
            else:
                raise Exception("User with email does not exist")

        user = authenticate(
            username=valid_request.validated_data["email"],
            password=valid_request.validated_data.get("password", None),
        )

        if not user:
            return Response(
                {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
            )

        access = get_access_token({"user_id": str(user.id)}, 1)
        user.last_login = datetime.now()
        user.save()

        add_user_Activity(user, "user logged in")
        return Response({"access_token": access}, status=status.HTTP_200_OK)


class UpdatePasswordView(ModelViewSet):
    serializer_class = UpdatePasswordSerializer
    http_method_names = ["post"]
    queryset = CreateUserView.queryset

    def create(self, request):
        valid_data = self.serializer_class(data=request.data)
        valid_data.is_valid(raise_exception=True)

        user = CustomUser.objects.filter(id=valid_data.validated_data["user_id"])

        if not user:
            raise Exception("User with id not found.")

        user = user[0]
        user.set_password(valid_data.validated_data["password"])
        user.save()

        add_user_Activity(user, "Created Password")
        return Response({"success": "User password is set."})


class MeView(ModelViewSet):
    serializer_class = CustomUserSerializer
    queryset = CreateUserView.queryset
    http_method_names = ["get"]
    permission_classes = (IsAuthenticatedCustom,)

    def list(self, request):
        data = self.serializer_class(request.user).data
        return Response(data)


class UserActivitiesView(ModelViewSet):
    serializer_class = UserActivitySerializer
    http_method_names = ["get"]
    queryset = UserActivities.objects.all().select_related("user")
    permission_classes = (IsAuthenticatedCustom,)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.method.lower() != "get":
            return self.queryset

        data = self.request.query_params.dict()

        data.pop("page", None)

        keyword = data.pop("keyword", None)

        results = self.queryset.filter(**data)

        if keyword:
            search_fields = (
                "fullname",
                "action",
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results


class UsersView(ModelViewSet):
    serializer_class = CustomUserSerializer
    http_method_names = ["get"]
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticatedCustom,)

    def list(self, _):
        users = self.queryset.filter(is_superuser=False)
        data = self.serializer_class(users, many=True).data
        return Response(data)
