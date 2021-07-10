import uuid
from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField
from django.db.models import Q
from django.dispatch import receiver
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files import File
import os
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import ArrayField
from django.dispatch import receiver
from superadmin.models import *


def make_thumbnail(image, size):
    im = Image.open(image)
    im = ImageOps.exif_transpose(im)
    im.convert("RGB")
    im.thumbnail(size)
    thumb_io = BytesIO()
    im.save(thumb_io, 'PNG', quality=75)
    thumbnail = File(thumb_io, name=image.name)
    return thumbnail


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, related_name="profile", on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to='user-avatar/original/%Y/%m/%d/', default=None, null=True, blank=True)

    def __str__(self):
        return self.user.email


@receiver(models.signals.pre_save, sender=UserProfile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_file = sender.objects.get(pk=instance.pk).avatar
    except sender.DoesNotExist:
        return False

    new_file = instance.avatar
    if old_file and not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


class ScannedImage(models.Model):
    user = models.OneToOneField(
        User, related_name="scanned_images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='scanned-image/%Y/%m/%d/')


@receiver(models.signals.post_delete, sender=ScannedImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=ScannedImage)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


class EmailToken(models.Model):
    tasks = (('EV', 'Email Verification'),
             ('RP', 'Reset Password'), ('SC', 'Staff Confirm'))
    user = models.ForeignKey(
        User, related_name="email_token", on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    task = models.CharField(max_length=2, choices=tasks)
    created_on = models.DateTimeField(auto_now_add=True)


class UserAddress(models.Model):
    STATUS = (('P', 'Primary'), ('S', 'Secondary'))
    user = models.ForeignKey(
        User, related_name="address", on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=STATUS, default='S')
    name = models.CharField(max_length=1024)
    info = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return self.user.email


class UserContact(models.Model):
    STATUS = (('P', 'Primary'), ('S', 'Secondary'))
    user = models.ForeignKey(
        User, related_name="contact", on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=STATUS, default='S')
    number = models.CharField(max_length=20)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return self.user.email


class UserGST(models.Model):
    STATUS = (('P', 'Primary'), ('S', 'Secondary'))
    user = models.ForeignKey(User, related_name="gst",
                             on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=STATUS, default='S')
    name = models.CharField(max_length=255)
    gst = models.CharField(max_length=50)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return self.user.email


class Company(models.Model):
    STATUS = (('V', 'Verification'), ('R', 'Running'), ('C', 'Close'), )
    user = models.OneToOneField(
        User, related_name="company", on_delete=models.CASCADE)
    parent = models.ForeignKey(
        ParentCategory, related_name="companies", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    gst = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=1024)
    status = models.CharField(max_length=1, choices=STATUS, default='V')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    company = models.ForeignKey(
        Company, related_name="categories", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to='category/original/%Y/%m/%d/', default=None, null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to='category/thumbnail/%Y/%m/%d/', default=None, null=True, blank=True, editable=False)
    slug = models.SlugField(max_length=255, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image:
            self.thumbnail = make_thumbnail(
                self.image, size=settings.CATEGORY_THUMBNAIL_SIZE)
        if self.name:
            numbering = 1
            slug = slugify(self.name)
            while Category.objects.filter((Q(company=self.company) & Q(slug=slug) & ~Q(id=self.pk))).exists():
                slug = slugify(self.name) + '-' + str(numbering)
                numbering += 1
            self.slug = slug
        super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=Category)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)


@receiver(models.signals.pre_save, sender=Category)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
        old_thumbnail = sender.objects.get(pk=instance.pk).thumbnail
    except sender.DoesNotExist:
        print(False)

    new_file = instance.image
    if old_file and not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
        if os.path.isfile(old_thumbnail.path):
            os.remove(old_thumbnail.path)


class Product(models.Model):
    company = models.ForeignKey(
        Company, related_name="products", on_delete=models.CASCADE)
    code = models.CharField(
        max_length=255, default=None, null=True, blank=True)
    brand = models.CharField(
        max_length=255, default=None, null=True, blank=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to='product/original/%Y/%m/%d/', default=None, blank=True, null=True)
    thumbnail = models.ImageField(
        upload_to='product/thumbnail/%Y/%m/%d/', editable=False)
    slug = models.SlugField(max_length=1024, editable=False)
    description = models.TextField()
    unit = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    sale_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(100)], editable=False)
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image:
            self.thumbnail = make_thumbnail(
                self.image, size=settings.PRODUCT_THUMBNAIL_SIZE)
        if self.name:
            numbering = 1
            slug = slugify(self.name)
            while Product.objects.filter((Q(company=self.company) & Q(slug=slug) & ~Q(id=self.pk))).exists():
                slug = slugify(self.name) + '-' + str(numbering)
                numbering += 1
            self.slug = slug
        if self.price and self.sale_price:
            self.discount = ((self.price - self.sale_price)
                             * 100) // self.price
        if not bool(self.code):
            self.code = self.slug
        super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=Product)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)


@receiver(models.signals.pre_save, sender=Product)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
        old_thumbnail = sender.objects.get(pk=instance.pk).thumbnail
    except sender.DoesNotExist:
        print(False)

    new_file = instance.image
    if old_file and not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
        if os.path.isfile(old_thumbnail.path):
            os.remove(old_thumbnail.path)


class ProductTag(models.Model):
    product = models.ForeignKey(
        Product, related_name="product_tags", on_delete=models.CASCADE)
    tag = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.product.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="product_images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product/original/%Y/%m/%d/')

    def __str__(self):
        return self.product.name


@receiver(models.signals.post_delete, sender=ProductImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


class Coupon(models.Model):
    company = models.ForeignKey(
        Company, related_name="coupons", on_delete=models.CASCADE)
    campaign = models.CharField(max_length=255)
    discount = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(100)])
    code = models.CharField(max_length=255)
    image = models.ImageField(upload_to='coupon/original/%Y/%m/%d/')
    thumbnail = models.ImageField(
        upload_to='coupon/thumbnail/%Y/%m/%d/', default=None, null=True, blank=True, editable=False)
    total = models.PositiveSmallIntegerField()
    used = models.PositiveSmallIntegerField(default=0)
    minimum = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    expiration_date = models.DateField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.thumbnail = make_thumbnail(
            self.image, size=settings.COUPON_THUMBNAIL_SIZE)
        super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=Coupon)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)


@receiver(models.signals.pre_save, sender=Coupon)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
        old_thumbnail = sender.objects.get(pk=instance.pk).thumbnail
    except sender.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
        if os.path.isfile(old_thumbnail.path):
            os.remove(old_thumbnail.path)


class Staff(models.Model):
    company = models.ForeignKey(
        Company, related_name="members", on_delete=models.CASCADE)
    member = models.OneToOneField(
        User, related_name="as_staff", on_delete=models.CASCADE)
    role = models.ForeignKey(StaffRole, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.member.email


class UserCart(models.Model):
    user = models.ForeignKey(User, related_name="cart",
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.user.email


class Order(models.Model):
    user = models.ForeignKey(
        User, related_name="user_orders", on_delete=models.CASCADE)
    vendor = models.ForeignKey(
        Company, related_name="company_orders", on_delete=models.CASCADE)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    transaction_id = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    customer_address = models.TextField()
    customer_contact = models.CharField(max_length=20)
    customer_business_name = models.CharField(
        max_length=255, default=None, null=True, blank=True)
    customer_business_gst = models.CharField(
        max_length=50, default=None, null=True, blank=True)
    discount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    remarks = models.CharField(
        max_length=1024, default=None, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='order/product/%Y/%m/%d/')
    description = models.TextField()
    unit = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField()


@receiver(models.signals.post_delete, sender=OrderProduct)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=OrderProduct)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
