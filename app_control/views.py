from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from .models import InvoiceItem

from inventory_api.custom_methods import IsAuthenticatedCustom
from user_control.models import CustomUser
from inventory_api.utils import CustomPagination, get_query
from .serializer import (
    InventoryGroupSerializer,
    Inventory,
    InventorySerializer,
    InventoryGroup,
    InventoryWithSum,
    Shop,
    ShopSerializer,
    Invoice,
    InvoiceSerializer,
    ShopWithAmountSerializer,
)
from rest_framework.response import Response
from django.db.models import Count, functions, Sum, F
import codecs
import csv


class InventoryView(ModelViewSet):
    queryset = Inventory.objects.select_related("group", "created_by")
    serializer_class = InventorySerializer
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
                "name",
                "created_by__email",
                "created_by__fullname",
                "group__name",
                "code",
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)


class InventoryGroupView(ModelViewSet):
    queryset = InventoryGroup.objects.select_related(
        "belongs_to", "created_by"
    ).prefetch_related("group_inventories")
    serializer_class = InventoryGroupSerializer
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
                "created_by__email",
                "created_by__fullname",
                "name",
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results.annotate(total_items=Count("group_inventories"))

    def create(self, request, *args, **kwargs):
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)


class ShopView(ModelViewSet):
    queryset = Shop.objects.select_related("created_by")
    serializer_class = ShopSerializer
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
                "created_by__email",
                "created_by__fullname",
                "group",
                "name",
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        request.data.update({"created_by_id": request.user.id})
        return super().create(request, *args, **kwargs)


class InvoiceView(ModelViewSet):
    queryset = Invoice.objects.select_related("created_by", "shop").prefetch_related(
        "invoice_items"
    )
    serializer_class = InvoiceSerializer
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
                "created_by__email",
                "created_by__fullname",
                "shop__name",
            )
            query = get_query(keyword, search_fields)
            results = results.filter(query)

        return results

    def create(self, request, *args, **kwargs):
        shop = 1
        if request.user.shop_id is not None:
            shop = request.user.shop_id
        request.data.update({"created_by_id": request.user.id, "shop_id": shop})
        return super().create(request, *args, **kwargs)


class SummaryView(ModelViewSet):
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    http_method_names = ("get",)

    def list(self, request, *args, **kwargs):
        total_inventory = InventoryView.queryset.filter(remaining__gt=0).count()
        total_groups = InventoryGroupView.queryset.count()
        total_shops = ShopView.queryset.count()
        total_users = CustomUser.objects.filter(is_superuser=False).count()

        return Response(
            {
                "total_inventory": total_inventory,
                "total_groups": total_groups,
                "total_shops": total_shops,
                "total_users": total_users,
            },
            status=status.HTTP_200_OK,
        )


class SalesPerformanceView(ModelViewSet):
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    http_method_names = ("get",)

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get("total", None)
        query = self.queryset

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(
                    inventory_invoices__created_at___range=[start_date, end_date]
                )

        items = query.annotate(
            sum_of_items=functions.Coalesce(Sum("inventory_invoices__quantity"), 0)
        ).order_by("-sum_of_items")[0:10]

        response_data = InventoryWithSum(items, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)


class SaleByShopView(ModelViewSet):
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    http_method_names = ("get",)

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get("total", None)
        monthly = query_data.get("monthly", None)
        query = ShopView.queryset

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(
                    sale_shop__created_at___range=[start_date, end_date]
                )
        if monthly:
            shops = (
                query.annotate(monthly=functions.TruncMonth("created_at"))
                .values("months", "name")
                .annotate(
                    amount_total=Sum(
                        F("sale_shop__invoice_items__quantity")
                        * F("sale_shop__invoice_items__amount")
                    )
                )
            )

        else:
            shops = query.annotate(
                amount_total=Sum(
                    F("sale_shop__invoice_items__quantity")
                    * F("sale_shop__invoice_items__amount")
                )
            ).order_by("-amount_total")

        response_data = ShopWithAmountSerializer(shops, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)


class PurchaseView(ModelViewSet):
    queryset = InvoiceView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    http_method_names = ("get",)

    def list(self, request, *args, **kwargs):
        query_data = request.query_params.dict()
        total = query_data.get("total", None)
        query = InvoiceItem.objects.prefetch_related("shop", "item")

        if not total:
            start_date = query_data.get("start_date", None)
            end_date = query_data.get("end_date", None)

            if start_date:
                query = query.filter(created_at___range=[start_date, end_date])

        query = query.aggregate(
            amount_total=Sum(F("amount") * F("quantity")), total=Sum("quantity")
        )

        return Response(
            {
                "price": "0.00"
                if not query.get("amount_total")
                else query.get("amount_total"),
                "count": 0 if not query.get("total") else query.get("total"),
            }
        )


class InventoryCSVLoaderView(ModelViewSet):
    queryset = InventoryView.queryset
    permission_classes = (IsAuthenticatedCustom,)
    http_method_names = ("post",)
    serializer_class = InventorySerializer

    def create(self, request, *args, **kwargs):
        try:
            data = request.FILES["data"]
        except Exception as e:
            raise Exception("You need to provide inventory CSV 'data'")

        inventory_items = []
        flag = False

        try:
            csv_reader = csv.reader(codecs.iterdecode(data, "utf-8"))
            for row in csv_reader:
                if not row[0] or not str.isdigit(row[0]):
                    continue
                valid_inventory = self.serializer_class(
                    data={
                        "group_id": row[0],
                        "total": row[1],
                        "name": row[2],
                        "price": row[3],
                        "photo": row[4],
                        "created_by_id": request.user.id,
                    }
                )
                valid_inventory.is_valid(raise_exception=True)
                old_data = Inventory.objects.filter(
                    name=valid_inventory.validated_data.get("name")
                )
                if len(old_data) > 0:
                    flag = True
                    old_data = old_data[0]
                    old_data.remaining += valid_inventory.validated_data.get("total")
                    old_data.total += valid_inventory.validated_data.get("total")
                    old_data.price = valid_inventory.validated_data.get("price")
                    old_data.save()
                else:
                    inventory_items.append(
                        {
                            "group_id": row[0],
                            "total": row[1],
                            "name": row[2],
                            "price": row[3],
                            "photo": row[4],
                            "created_by_id": request.user.id,
                        }
                    )

        except Exception as e:
            raise Exception(e)
        if len(inventory_items) < 0 and not flag:
            raise Exception("Provide csv file")

        if len(inventory_items) > 0:
            data_validation = self.serializer_class(data=inventory_items, many=True)
            data_validation.is_valid(raise_exception=True)
            data_validation.save()

        return Response({"success": "Inventory Items added successfully"})
