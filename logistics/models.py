from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from django.contrib.auth.models import User

class Order(models.Model):
    STATUS_CHOICES = (
        ("in_progress", "In progress"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )
    depart_from = models.CharField(max_length=255, blank=True, default="")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)

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
    