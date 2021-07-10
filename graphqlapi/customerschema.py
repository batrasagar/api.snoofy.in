import graphene
from graphene import relay
from django.db.models import Q, Sum, Count, Min, F
from datetime import date
from django.contrib.auth.models import User
from django_filters import FilterSet, OrderingFilter
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from restapi.models import *
from superadmin.models import *

def get_company_by_user(self, info):
    user = info.context.user
    return Company.objects.get(user=user)

def get_filtered_products(self, info):
    products = Product.objects.filter(company__status='R', is_active=True)
    if self['company']:
        com = Company.objects.get(slug=self['company'])
        products = Product.objects.filter(company=com, is_active=True)
        
    if self['categorySlug']:
        filter = (
            Q(product_tags__tag__slug=self['categorySlug'])    
        )
        products = products.filter(filter)

    if self['search']:
        filter = (
            Q(name__icontains=self['search'])
        )
        products = products.filter(filter)

    return products.distinct()

def get_all_filtered_products(self, info):
    products = Product.objects.filter(company__status='R', is_active=True)
    if self['parentCategorySlug']:
        filter = (
            Q(company__parent__slug=self['parentCategorySlug'])    
        )
        products = products.filter(filter)

    if self['search']:
        filter = (
            Q(name__icontains=self['search'])
        )
        products = products.filter(filter)

    return products.distinct()

class ParentType(DjangoObjectType):
    class Meta:
        model = ParentCategory
        fields = "__all__"

class PaymentMethodType(DjangoObjectType):
    class Meta:
        model = PaymentMethod
        fields = "__all__"

class OrderStatusType(DjangoObjectType):
    class Meta:
        model = OrderStatus
        fields = "__all__"

class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)

class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile
        fields = "__all__"

class UserAddressType(DjangoObjectType):
    class Meta:
        model = UserAddress
        fields = "__all__"

class UserGSTType(DjangoObjectType):
    class Meta:
        model = UserGST
        fields = "__all__"

class UserContactType(DjangoObjectType):
    class Meta:
        model = UserContact
        fields = "__all__"

class UserCartType(DjangoObjectType):
    class Meta:
        model = UserCart
        fields = "__all__"

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"

class CouponType(DjangoObjectType):
    class Meta:
        model = Coupon
        fields = "__all__"

class StaffRoleType(DjangoObjectType):
    class Meta:
        model = StaffRole
        fields = "__all__"

class CompanyType(DjangoObjectType):
    class Meta:
        model = Company
        fields = "__all__"

class StaffType(DjangoObjectType):
    class Meta:
        model = Staff
        fields = "__all__"

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class ProductTagType(DjangoObjectType):
    class Meta:
        model = ProductTag
        fields = "__all__"

class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = "__all__"

class ProductSchema(graphene.ObjectType):
    total_count = graphene.Int()
    is_first = graphene.Boolean()
    items = graphene.List(ProductType)

    def resolve_items(self, info):
        products = get_filtered_products(self, info)
        if self['skip']:
            products = products[self['skip']:]
        if self['first']:
            products = products[:self['first']]
        return products

    def resolve_total_count(self, info):
        products = get_filtered_products(self, info)
        return len(products)

    def resolve_is_first(self, info):
        if self['skip']:
            return self['skip']==0
        return True

class AllProductSchema(graphene.ObjectType):
    total_count = graphene.Int()
    is_first = graphene.Boolean()
    items = graphene.List(ProductType)

    def resolve_items(self, info):
        products = get_all_filtered_products(self, info)
        if self['skip']:
            products = products[self['skip']:]
        if self['first']:
            products = products[:self['first']]
        return products

    def resolve_total_count(self, info):
        products = get_all_filtered_products(self, info)
        return len(products)

    def resolve_is_first(self, info):
        if self['skip']:
            return self['skip']==0
        return True

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"

class OrderProductType(DjangoObjectType):
    class Meta:
        model = OrderProduct
        fields = "__all__"

class OrdersSchema(graphene.ObjectType):
    total_count = graphene.Int()
    is_first = graphene.Boolean()
    items = graphene.List(OrderType)

    def resolve_items(self, info):
        orders = Order.objects.filter(user=info.context.user)
        if self['offset']:
            orders = orders[self['offset']:]
        if self['limit']:
            orders = orders[:self['limit']]
        return orders

    def resolve_total_count(self, info):
        orders = Order.objects.filter(user=info.context.user)
        return len(orders)

    def resolve_is_first(self, info):
        if self['offset']:
            return self['offset']==0
        return True

class CustomerType(DjangoObjectType):
    orders_count = graphene.Int()
    orders_amount = graphene.Int()
    joined_on = graphene.DateTime()
    
    class Meta:
        model = User
        exclude = ('password',)

class QueryWithAuth(graphene.ObjectType):
    user = graphene.Field(UserType)
    parentCategories = graphene.List(ParentType)
    categories = graphene.List(CategoryType, company=graphene.String())
    coupons = graphene.List(CouponType, company=graphene.String())
    coupon = graphene.Field(CouponType, code=graphene.String())
    allproducts = graphene.Field(AllProductSchema, parentCategorySlug=graphene.String(), search=graphene.String(), first=graphene.Int(), skip=graphene.Int())
    products = graphene.Field(ProductSchema, company=graphene.String(), categorySlug=graphene.String(), search=graphene.String(), first=graphene.Int(), skip=graphene.Int())
    product = graphene.Field(ProductType, company=graphene.String(), slug=graphene.String())
    company = graphene.Field(CompanyType, slug=graphene.String())
    orders = graphene.Field(OrdersSchema, limit=graphene.Int(), offset=graphene.Int())
    order = graphene.List(OrderType, ordersIds=graphene.String())

    def resolve_user(self, info):
        return info.context.user

    def resolve_parentCategories(self, info):
        return ParentCategory.objects.all()

    def resolve_categories(self, info, company=None):
        if company:
            com = Company.objects.get(slug=company)
            return Category.objects.filter(company=com)
        return None

    def resolve_coupons(self, info, company=None):
        if company:
            com = Company.objects.get(slug=company)
            coupons = Coupon.objects.filter(company=com, used__lt=F('total'), expiration_date__gt=date.today())
            return coupons
        return None

    def resolve_coupon(self, info, code=None):
        if code:
            coupon = Coupon.objects.get(code=code, used__lt=F('total'), expiration_date__gt=date.today())
            return coupon
        return None

    def resolve_allproducts(self, info, parentCategorySlug=None, search=None, first=None, skip=None):
        return {'parentCategorySlug': parentCategorySlug, 'search': search, 'first': first, 'skip': skip}

    def resolve_products(self, info, company=None, categorySlug=None, search=None, first=None, skip=None):
        return {'company': company, 'categorySlug': categorySlug, 'search': search, 'first': first, 'skip': skip}

    def resolve_product(self, info, company=None, slug=None):
        if company and slug:
            com = Company.objects.get(slug=company)
            return Product.objects.get(company=com, slug=slug, is_active=True)
        return None

    def resolve_company(self, info, slug=None):
        if slug:
            return Company.objects.get(slug=slug, status='R')
        return None

    def resolve_orders(self, info, limit=None, offset=None):
        return {'limit': limit, 'offset': offset}

    def resolve_order(self, info, ordersIds=None):
        if ordersIds:
            ids = list(map(int, ordersIds.split(',')))
            orders = Order.objects.filter(id__in=ids, user=info.context.user)
            return orders
        return None

class QueryWithoutAuth(graphene.ObjectType):
    user = graphene.Field(UserType)
    parentCategories = graphene.List(ParentType)
    categories = graphene.List(CategoryType, company=graphene.String())
    coupons = graphene.List(CouponType, company=graphene.String())
    coupon = graphene.Field(CouponType, code=graphene.String())
    allproducts = graphene.Field(AllProductSchema, parentCategorySlug=graphene.String(), search=graphene.String(), first=graphene.Int(), skip=graphene.Int())
    products = graphene.Field(ProductSchema, company=graphene.String(), categorySlug=graphene.String(), search=graphene.String(), first=graphene.Int(), skip=graphene.Int())
    product = graphene.Field(ProductType, company=graphene.String(), slug=graphene.String())
    company = graphene.Field(CompanyType, slug=graphene.String())
    orders = graphene.List(OrderType)
    order = graphene.List(OrderType, ordersIds=graphene.String())

    def resolve_user(self, info):
        return None

    def resolve_parentCategories(self, info):
        return ParentCategory.objects.all()

    def resolve_categories(self, info, contentType=None, company=None):
        if company:
            com = Company.objects.get(slug=company)
            return Category.objects.filter(company=com)
        return None

    def resolve_coupons(self, info, company=None):
        if company:
            com = Company.objects.get(slug=company)
            coupons = Coupon.objects.filter(company=com, used__lt=F('total'), expiration_date__gt=date.today())
            return coupons
        return None
        
    def resolve_coupon(self, info, code=None):
        return None

    def resolve_allproducts(self, info, parentCategorySlug=None, search=None, first=None, skip=None):
        return {'parentCategorySlug': parentCategorySlug, 'search': search, 'first': first, 'skip': skip}

    def resolve_products(self, info, company=None, categorySlug=None, search=None, first=None, skip=None):
        return {'company': company, 'categorySlug': categorySlug, 'search': search, 'first': first, 'skip': skip}

    def resolve_product(self, info, company=None, slug=None):
        if company and slug:
            com = Company.objects.get(slug=company)
            return Product.objects.get(company=com, slug=slug, is_active=True)
        return None

    def resolve_company(self, info, slug=None):
        if slug:
            return Company.objects.get(slug=slug, status='R')
        return None

    def resolve_orders(self, info, type='user', status=None, limit=None, search=None):
        return None

    def resolve_order(self, info, ordersIds=None):
        return None

schema_with_auth = graphene.Schema(query=QueryWithAuth)
schema_without_auth = graphene.Schema(query=QueryWithoutAuth)

