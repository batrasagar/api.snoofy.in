from django.contrib import admin
from django.contrib.sites.models import Site
from .models import *

# Register your models here.


class UserProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user')
    list_display_links = ('user',)


class ScannedImageAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user')


class EmailTokenAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'token')
    list_display = ('id', 'user', 'task')
    list_display_links = ('user',)


class UserContactAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'number', 'type')
    list_display_links = ('user',)


class UserAddressAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'name', 'type')
    list_display_links = ('user',)


class UserGSTAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'name', 'type')
    list_display_links = ('user',)


class UserCartAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'product', 'quantity')
    list_display_links = ('user',)


class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'slug')
    list_display = ('id', 'company', 'name')
    list_display_links = ('company',)


class CompanyAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'name', 'status')
    list_display_links = ('user',)


class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'slug', 'discount')
    list_display = ('id', 'company', 'name')
    list_display_links = ('company', 'name')


class CouponAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'company', 'campaign', 'code')
    list_display_links = ('company', 'campaign')


class StaffAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'company', 'member', 'role')
    list_display_links = ('company', 'member')


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'vendor')
    list_display_links = ('user', 'vendor')


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ScannedImage, ScannedImageAdmin)
admin.site.register(UserAddress, UserAddressAdmin)
admin.site.register(UserContact, UserContactAdmin)
admin.site.register(UserGST, UserGSTAdmin)
admin.site.register(UserCart, UserCartAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(ProductTag)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(EmailToken, EmailTokenAdmin)

admin.site.unregister(Site)


class SiteAdmin(admin.ModelAdmin):
    fields = ('id', 'name', 'domain')
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'domain')
    list_display_links = ('name',)
    search_fields = ('name', 'domain')


admin.site.register(Site, SiteAdmin)
