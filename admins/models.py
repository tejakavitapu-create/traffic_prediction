from django.db import models


class RegisterUserTable(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)
    password = models.CharField(max_length=10)
    address = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
