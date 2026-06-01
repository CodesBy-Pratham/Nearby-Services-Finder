from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    USER = "USER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"

    ROLE_CHOICES = (
        (USER, "User"),
        (STAFF, "Staff"),
        (ADMIN, "Admin"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USER)

    def __str__(self):
        return self.username
