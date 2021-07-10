from django.db import models

class ParentCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=500, unique=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

class StaffRole(models.Model):
    code = models.CharField(max_length=2, unique=True)
    role = models.CharField(max_length=255)
    class Meta:
        ordering = ['role']
    def __str__(self):
        return self.role

class OrderStatus(models.Model):
    code = models.CharField(max_length=2, unique=True)
    status = models.CharField(max_length=500)
    class Meta:
        ordering = ['status']
    def __str__(self):
        return self.status

class PaymentMethod(models.Model):
    code = models.CharField(max_length=3, unique=True)
    method = models.CharField(max_length=500)
    class Meta:
        ordering = ['method']
    def __str__(self):
        return self.method
