from django.db import models
from user_control.views import add_user_Activity
from user_control.models import CustomUser


class InventoryGroup(models.Model):
    created_by = models.ForeignKey(
        CustomUser,
        null=True,
        related_name="inventory_groups",
        on_delete=models.SET_NULL,
    )
    name = models.CharField(unique=True, max_length=100)
    belongs_to = models.ForeignKey(
        "self",
        null=True,
        on_delete=models.SET_NULL,
        related_name="groups_relations",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.old_name = self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is not None
        action = f"added new group - '{self.name}'"
        if is_new:
            action = f"updated new group - '{self.old_name}' to '{self.name}'"
        super().save(*args, **kwargs)
        add_user_Activity(self.created_by, action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted group - '{self.name}'"
        super().delete(*args, **kwargs)
        add_user_Activity(created_by, action)

    def __str__(self) -> str:
        return self.name


class Inventory(models.Model):
    created_by = models.ForeignKey(
        CustomUser,
        null=True,
        related_name="user_inventories",
        on_delete=models.SET_NULL,
    )
    code = models.CharField(null=True, blank=True, max_length=10, unique=True)
    photo = models.TextField(blank=True, null=True)
    group = models.ForeignKey(
        InventoryGroup,
        on_delete=models.SET_NULL,
        related_name="group_inventories",
        null=True,
    )
    total = models.PositiveIntegerField()
    remaining = models.PositiveIntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.remaining = self.total
        super().save(*args, **kwargs)

        if is_new:
            id_length = len(str(self.id))
            code_length = 6 - id_length
            zeros = "".join("0" for i in range(code_length))
            self.code = f"ITEM{zeros}{self.id}"
            self.save()
        action = f"added new inventory item with code - '{self.code}'"
        if not is_new:
            action = f"updated inventory item with code - '{self.code}'"

        add_user_Activity(self.created_by, action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted inventory item - '{self.code}'"
        super().delete(*args, **kwargs)
        add_user_Activity(created_by, action)

    def __str__(self) -> str:
        return f"{self.name} - {self.code}"


class Shop(models.Model):
    created_by = models.ForeignKey(
        CustomUser,
        null=True,
        related_name="shop",
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.old_name = self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is not None
        action = f"added new shop - '{self.name}'"
        if is_new:
            action = f"updated new shop - '{self.old_name}' to '{self.name}'"
        super().save(*args, **kwargs)
        add_user_Activity(self.created_by, action)

    def delete(self, *args, **kwargs):
        created_by = self.created_by
        action = f"deleted shop - '{self.name}'"
        super().delete(*args, **kwargs)
        add_user_Activity(created_by, action)

    def __str__(self) -> str:
        return self.name


class Invoice(models.Model):
    created_by = models.ForeignKey(
        CustomUser,
        null=True,
        related_name="invoice",
        on_delete=models.SET_NULL,
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.SET_NULL, related_name="sale_shop", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        is_new = self.pk is not None
        action = f"added new invoice"
        super().save(*args, **kwargs)
        add_user_Activity(self.created_by, action)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name="invoice_items", on_delete=models.CASCADE
    )
    item = models.ForeignKey(
        Inventory,
        null=True,
        related_name="inventory_invoices",
        on_delete=models.SET_NULL,
    )
    item_name = models.CharField(max_length=255, null=True)
    item_code = models.CharField(max_length=20, null=True)
    quantity = models.PositiveIntegerField()
    amount = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if self.item.remaining < self.quantity:
            raise Exception(
                f"item with code - {self.item.code} does not have enough quantity"
            )
        self.item_name = self.item.name
        self.item_code = self.item.code
        self.amount = self.item.price * self.quantity
        self.item.remaining = self.item.remaining - self.quantity
        self.item.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_code} - {self.quantity}"
