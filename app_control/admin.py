from django.contrib import admin
from .models import Inventory, InventoryGroup, Shop, InvoiceItem, Invoice

# Register your models here.
admin.site.register((InventoryGroup, Inventory, Shop, InvoiceItem, Invoice))
