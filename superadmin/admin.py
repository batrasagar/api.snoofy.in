from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(ParentCategory)
admin.site.register(StaffRole)
admin.site.register(OrderStatus)
admin.site.register(PaymentMethod)