from django.urls import path, include
from .views import (
    InventoryView,
    ShopView,
    SummaryView,
    SaleByShopView,
    PurchaseView,
    InventoryGroupView,
    SalesPerformanceView,
    InvoiceView,
    InventoryCSVLoaderView,
)
from rest_framework.routers import DefaultRouter


router = DefaultRouter(trailing_slash=False)
router.register("inventory", InventoryView, "inventory")
router.register("shop", ShopView, "shop")
router.register("inventory_csv", InventoryCSVLoaderView, "inventory_csv")
router.register("summary", SummaryView, "summary")
router.register("purchase_summary", PurchaseView, "purchase_summary")
router.register("sales_by_shop", SaleByShopView, "sales_by_shop")
router.register("top_selling", SalesPerformanceView, "top_selling")
router.register("invoice", InvoiceView, "invoice")
router.register("groups", InventoryGroupView, "groups")


urlpatterns = [path("app/", include(router.urls))]
