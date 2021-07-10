from rest_framework import serializers
from rest_auth.serializers import LoginSerializer
from .models import *
from superadmin.models import *
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class ParentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentCategory
        fields = "__all__"


class StaffRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffRole
        fields = "__all__"


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = UserProfile
        fields = "__all__"


class ScannedImageSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = ScannedImage
        fields = "__all__"


class UserAddressSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = UserAddress
        fields = "__all__"


class UserContactSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = UserContact
        fields = "__all__"


class UserGSTSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = UserGST
        fields = "__all__"


class UserCartSerializer(serializers.ModelSerializer):
    queryset_user = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset_user, many=False, read_only=False)

    queryset_product = Product.objects.all()
    product = serializers.PrimaryKeyRelatedField(
        queryset=queryset_product, many=False, read_only=False)

    class Meta:
        model = UserCart
        fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):
    queryset_user = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset_user, many=False, read_only=False)
    queryset_parent_category = ParentCategory.objects.all()
    parent = serializers.PrimaryKeyRelatedField(
        queryset=queryset_parent_category, many=False, read_only=False)

    class Meta:
        model = Company
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    queryset = Company.objects.all()
    company = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = Category
        fields = "__all__"


class ProductTagSerializer(serializers.ModelSerializer):
    queryset_product = Product.objects.all()
    product = serializers.PrimaryKeyRelatedField(
        queryset=queryset_product, many=False, read_only=False)
    queryset_tag = Category.objects.all()
    tag = serializers.PrimaryKeyRelatedField(
        queryset=queryset_tag, many=False, read_only=False)

    class Meta:
        model = ProductTag
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer):
    queryset = Product.objects.all()
    product = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = ProductImage
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    queryset_company = Company.objects.all()
    company = serializers.PrimaryKeyRelatedField(
        queryset=queryset_company, many=False, read_only=False)

    class Meta:
        model = Product
        fields = "__all__"


class CouponSerializer(serializers.ModelSerializer):
    queryset = Company.objects.all()
    company = serializers.PrimaryKeyRelatedField(
        queryset=queryset, many=False, read_only=False)

    class Meta:
        model = Coupon
        fields = "__all__"


class StaffSerializer(serializers.ModelSerializer):
    queryset_company = Company.objects.all()
    company = serializers.PrimaryKeyRelatedField(
        queryset=queryset_company, many=False, read_only=False)
    queryset_member = User.objects.all()
    member = serializers.PrimaryKeyRelatedField(
        queryset=queryset_member, many=False, read_only=False)
    queryset_role = StaffRole.objects.all()
    role = serializers.PrimaryKeyRelatedField(
        queryset=queryset_role, many=False, read_only=False)

    class Meta:
        model = Staff
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    queryset_vendor = Company.objects.all()
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=queryset_vendor, many=False, read_only=False)
    queryset_user = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(
        queryset=queryset_user, many=False, read_only=False)
    queryset_status = OrderStatus.objects.all()
    status = serializers.PrimaryKeyRelatedField(
        queryset=queryset_status, many=False, read_only=False)
    queryset_payment = PaymentMethod.objects.all()
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=queryset_payment, many=False, read_only=False)

    class Meta:
        model = Order
        fields = "__all__"


class OrderProductSerializer(serializers.ModelSerializer):
    queryset_order = Order.objects.all()
    order = serializers.PrimaryKeyRelatedField(
        queryset=queryset_order, many=False, read_only=False)

    class Meta:
        model = OrderProduct
        fields = "__all__"
