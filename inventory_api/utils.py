import re
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from user_control.models import CustomUser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q


def get_access_token(payload, expiry):
    token = jwt.encode(
        {"exp": datetime.now() + timedelta(days=expiry), **payload},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return token


def decode_jwt(payload):
    if not payload:
        return None

    token = payload[7:]
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
    except:
        return None

    if decoded:
        try:
            return CustomUser.objects.get(id=decoded.get("user_id", None))
        except:
            return None


class CustomPagination(PageNumberPagination):
    page_size = 10


def normalize_query(
    query_string,
    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
    normspace=re.compile(r"\s{2,}").sub,
):
    return [normspace(" ", (t[0] or t[1]).strip()) for t in findterms(query_string)]


def get_query(query_string, search_fields):
    query = None
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query

        return query
