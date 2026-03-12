from django.conf import settings
from django.db import models


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("picked_up", "Picked up"),
        ("in_transit", "In transit"),
        ("out_for_delivery", "Out for delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    depart_from = models.CharField(max_length=255, blank=True, default="")
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    address = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    start_lat = models.FloatField(null=True, blank=True)
    start_lng = models.FloatField(null=True, blank=True)
    dest_lat = models.FloatField(null=True, blank=True)
    dest_lng = models.FloatField(null=True, blank=True)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)

    estimated_delivery = models.DateTimeField(null=True, blank=True)
    tracking_note = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class Profile(models.Model):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("admin", "Admin"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"