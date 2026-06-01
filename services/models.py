from django.contrib.gis.db import models
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=255)

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="services"
    )

    location = models.PointField(srid=4326, geography=True)

    rating = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="services"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
