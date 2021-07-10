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


def get_company_by_staff(self, info):
    filter = (Q(members__member=info.context.user) & (
        Q(members__role__code='AD') | Q(members__role__code='MA')))
    return Company.objects.filter(filter)[0]


def get_company_by_staff_admin(self, info):
    filter = (Q(members__member=info.context.user)
              & Q(members__role__code='AD'))
    return Company.objects.filter(filter)[0]


def get_filtered_products(self, info):
    products = Product.objects.filter(company=get_company_by_staff(self, info))
    if self['isActive']:
        filter = (
            Q(is_active=False)
        )
        if self['isActive'] == 2:
            filter = (
                Q(is_active=True)
            )
        products = products.filter(filter)

    if self['tags']:
        filter = (
            Q(product_tags__tag__in=list(map(int, self['tags'].split(','))))
        )
        products = products.filter(filter)
    if self['search']:
        filter = (
            Q(name__icontains=self['search'])
        )
        products = products.filter(filter)
    if self['order']:
        products = products.order_by(self['order'])
    return products.distinct()


def get_filtered_orders(self, info):
    orders = Order.objects.filter(vendor=get_company_by_staff(self, info))
    if self['search']:
        filter = (
            Q(customer_address__icontains=self['search'])
        )
        orders = orders.filter(filter)
    if self['status']:
        filter = (
            Q(status=self['status'])
        )
        orders = orders.filter(filter)
    if self['orderlimit']:
        orders = orders.order_by('-created_on')
        orders = orders[:self['orderlimit']]
    return orders


def get_filtered_customers(self, info):
    company = get_company_by_staff(self, info)
    filter_vendor = Q(user_orders__vendor=company)
    if self['search']:
        filter = (Q(user_orders__vendor=company) & ((Q(contact__type='P') & Q(
            contact__number__icontains=self['search'])) | Q(first_name__icontains=self['search'])))
    else:
        filter = filter_vendor
    customers = User.objects.filter(filter).distinct().annotate(orders_count=Count('user_orders', filter=filter_vendor, distinct=True), orders_amount=Sum(
        'user_orders__amount', filter=filter_vendor), joined_on=Min('user_orders__created_on', filter=filter_vendor))
    if self['order']:
        customers = customers.order_by(self['order'])
    return customers


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


class UserContactType(DjangoObjectType):
    class Meta:
        model = UserContact
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
        return len(products.distinct())

    def resolve_is_first(self, info):
        if self['skip']:
            return self['skip'] == 0
        return True


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


class OrderProductType(DjangoObjectType):
    class Meta:
        model = OrderProduct
        fields = "__all__"


class OrderSchema(graphene.ObjectType):
    total_count = graphene.Int()
    is_first = graphene.Boolean()
    items = graphene.List(OrderType)

    def resolve_items(self, info):
        orders = get_filtered_orders(self, info)
        if self['offset']:
            orders = orders[self['offset']:]
        if self['limit']:
            orders = orders[:self['limit']]
        return orders

    def resolve_total_count(self, info):
        orders = get_filtered_orders(self, info)
        return len(orders)

    def resolve_is_first(self, info):
        if self['offset']:
            return self['offset'] == 0
        return True


class CustomerType(DjangoObjectType):
    orders_count = graphene.Int()
    orders_amount = graphene.Float()
    joined_on = graphene.DateTime()

    class Meta:
        model = User
        exclude = ('password',)


class CustomerSchema(graphene.ObjectType):
    total_count = graphene.Int()
    is_first = graphene.Boolean()
    items = graphene.List(CustomerType)

    def resolve_items(self, info):
        customers = get_filtered_customers(self, info)
        if self['offset']:
            customers = customers[self['offset']:]
        if self['limit']:
            customers = customers[:self['limit']]
        return customers

    def resolve_total_count(self, info):
        customers = get_filtered_customers(self, info)
        return len(customers)

    def resolve_is_first(self, info):
        if self['offset']:
            return self['offset'] == 0
        return True


class Query(graphene.ObjectType):
    user = graphene.Field(UserType)
    company = graphene.Field(CompanyType)
    categories = graphene.List(CategoryType, search=graphene.String())
    coupons = graphene.List(
        CouponType, search=graphene.String(), status=graphene.Int())
    staffs = graphene.List(
        StaffType, search=graphene.String(), role=graphene.Int())
    product = graphene.Field(ProductType, id=graphene.Int())
    products = graphene.Field(ProductSchema, search=graphene.String(), tags=graphene.String(
    ), order=graphene.String(), isActive=graphene.Int(), first=graphene.Int(), skip=graphene.Int())
    orders = graphene.Field(OrderSchema, status=graphene.Int(), orderlimit=graphene.Int(
    ), search=graphene.String(), limit=graphene.Int(), offset=graphene.Int())
    customers = graphene.Field(CustomerSchema, search=graphene.String(
    ), order=graphene.String(), limit=graphene.Int(), offset=graphene.Int())

    def resolve_user(self, info):
        company = get_company_by_staff(self, info)
        return info.context.user

    def resolve_company(self, info):
        return get_company_by_staff(self, info)

    def resolve_categories(self, info, search=None):
        categories = Category.objects.filter(
            company=get_company_by_staff(self, info))
        if search:
            filter = (
                Q(name__icontains=search) | Q(slug__icontains=search)
            )
            categories = categories.filter(filter)
        return categories

    def resolve_coupons(self, info, search=None, status=None):
        coupons = Coupon.objects.filter(
            company=get_company_by_staff(self, info))
        if search:
            filter = (
                Q(campaign__icontains=search) | Q(code__icontains=search)
            )
            coupons = coupons.filter(filter)
        if status:
            if status == 1:
                filter = (
                    ~Q(used__lt=F('total')) | Q(
                        expiration_date__lt=date.today())
                )
            else:
                filter = (
                    Q(used__lt=F('total')) & Q(
                        expiration_date__gt=date.today())
                )
            coupons = coupons.filter(filter)
        return coupons

    def resolve_staffs(self, info, search=None, role=None):
        company = get_company_by_staff_admin(self, info)
        filter = (Q(company=company) & Q(is_active=True) & ~Q(
            member=company.user) & ~Q(member=info.context.user))
        staffs = Staff.objects.filter(filter)
        if search:
            filter = (
                Q(member__first_name__icontains=search) |
                Q(member__email__icontains=search) |
                (Q(member__contact__type='P') & Q(
                    member__contact__number__icontains=search))
            )
            staffs = staffs.filter(filter)
        if role:
            filter = (
                Q(role=role)
            )
            staffs = staffs.filter(filter)
        return staffs.distinct()

    def resolve_product(self, info, id=None):
        if id:
            product = Product.objects.get(
                company=get_company_by_staff(self, info), pk=id)
            return product
        return None

    def resolve_products(self, info, search=None, tags=None, order=None, isActive=None, first=None, skip=None):
        return {'search': search, 'tags': tags, 'order': order, 'isActive': isActive, 'first': first, 'skip': skip}

    def resolve_orders(self, info, status=None, orderlimit=None, search=None, limit=None, offset=None):
        return {'status': status, 'orderlimit': orderlimit, 'search': search, 'limit': limit, 'offset': offset}

    def resolve_customers(self, info, search=None, order=None, limit=None, offset=None):
        return {'search': search, 'order': order, 'limit': limit, 'offset': offset}


schema = graphene.Schema(query=Query)
