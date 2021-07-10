from django.shortcuts import render
from rest_auth.views import LoginView
from firebase_admin import db
import time
from django.core.files import File
import urllib
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
import django.contrib.auth.password_validation as validators
from django.db.models import Q
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from rest_framework import generics, mixins, filters, status, exceptions
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt, csrf_protect
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.utils.translation import ugettext_lazy as _
from .models import *
from django.conf import settings
from superadmin.models import *
from .serializers import *
# Create your views here.


def get_company_by_staff(self, request):
    filter = (Q(members__member=request.user) & (
        Q(members__role__code='AD') | Q(members__role__code='MA')))
    return Company.objects.filter(filter)[0]


def get_company_by_staff_admin(self, request):
    filter = (Q(members__member=request.user) & Q(members__role__code='AD'))
    return Company.objects.filter(filter)[0]


def send_email(user, task, company_data=None):
    email_token, _ = EmailToken.objects.get_or_create(user=user, task=task)
    from_email = settings.EMAIL_HOST_USER
    to_email = [user.email]

    if task == 'EV':
        mail_subject = 'Email Verification'
        url = settings.FRONTEND_URL+"/email-verify/?user=" + \
            user.username+"&key="+str(email_token.token)
        message = get_template('email_verify.html').render(
            {'username': user.first_name, 'url': url})
    elif task == 'SC':
        mail_subject = 'Staff Confirmation'
        accept_url = settings.FRONTEND_URL+"/staff-confirm/?user=" + \
            user.username+"&key="+str(email_token.token)+"&response=accept"
        decline_url = settings.FRONTEND_URL+"/staff-confirm/?user=" + \
            user.username+"&key="+str(email_token.token)+"&response=decline"
        message = get_template('staff_confirm.html').render({'username': user.first_name, 'accept_url': accept_url,
                                                             'decline_url': decline_url, 'company_username': company_data.user.first_name, 'company_name': company_data.name})
    elif task == 'RP':
        mail_subject = 'Reset Password'
        url = settings.FRONTEND_URL+"/reset-pass/?user=" + \
            user.username+"&key="+str(email_token.token)
        message = get_template('pass_reset.html').render(
            {'username': user.first_name, 'url': url})

    msg = EmailMessage(
        mail_subject,
        message,
        from_email,
        to_email,
    )
    msg.content_subtype = "html"
    msg.send()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TokenVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(status=status.HTTP_200_OK)


class RegisterUserView(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                users = User.objects.filter(username=data['email'])
                if not users.exists():
                    user = User.objects.create(
                        username=data['email'], email=data['email'], first_name=data['name'])
                    validators.validate_password(
                        password=request.data['password'])
                    user.set_password(data['password'])
                    user.is_active = not settings.EMAIL_TASKS_REQUIRED
                    user.save()

                elif users[0].is_active:
                    return Response({'error': 'User with this email already exists'}, status=status.HTTP_404_NOT_FOUND)

                else:
                    user = users[0]

                msg = 'User Registered successfully'
                if settings.EMAIL_TASKS_REQUIRED:
                    send_email(user, 'EV')
                    msg = 'Email verification link has been sent to your registered email id'
                return Response({'success': msg}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'error': e.messages[0]}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'An error occurred. Please try again!'}, status=status.HTTP_404_NOT_FOUND)


class SuggestedSlugCompanyView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        name = request.data['name']
        try:
            numbering = 1
            slug = slugify(name)
            while Company.objects.filter(slug=slug).exists():
                slug = slugify(name) + '-' + str(numbering)
                numbering += 1
            return Response({'success': 'Company Registration Successful', 'slug': slug}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'An error occurred. Please try again!'}, status=status.HTTP_404_NOT_FOUND)


class EmailVerifyView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            with transaction.atomic():
                username = request.data['user']
                key = request.data['key']
                user = User.objects.get(username=username)
                email_token = EmailToken.objects.get(user=user, task='EV')
                if str(email_token.token) == str(key):
                    user.is_active = True
                    user.save()
                    email_token.delete()
                    return Response(status=status.HTTP_200_OK)
                return Response(status=status.HTTP_404_NOT_FOUND)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ResetPasswordEmailSendView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            username = request.data['email']
            users = User.objects.filter(username=username)
            if not users.exists():
                return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
            send_email(users[0], 'RP')
            return Response({'success': 'Password reset link sent'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'An error occurred. Please try again!'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordEmailResponseView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            with transaction.atomic():
                username = request.data['user']
                key = request.data['key']
                password = request.data['password']
                user = User.objects.get(username=username)
                email_token = EmailToken.objects.get(user=user, task='RP')
                if str(email_token.token) == str(key):
                    validators.validate_password(password=password)
                    user1 = User.objects.get(username=username)
                    user1.set_password(password)
                    user1.save()
                    email_token.delete()
                    return Response(status=status.HTTP_200_OK)
                return Response({'error': 'Error occurred!'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'error': e.messages[0]}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'Error occurred!'}, status=status.HTTP_404_NOT_FOUND)


class RegisterCompanyView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                data['user'] = request.user.pk
                if Company.objects.filter(slug=data['slug']).exists():
                    return Response({'error': 'Slug is already registered with another company.'}, status=status.HTTP_404_NOT_FOUND)
                if Company.objects.filter(gst=data['gst']).exists():
                    return Response({'error': 'GSTIN is already registered with another company.'}, status=status.HTTP_404_NOT_FOUND)
                serializer = CompanySerializer(data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                role = StaffRole.objects.get(code='AD').id
                staff_data = {'member': request.user.id,
                              'company': serializer.data['id'], 'role': role, 'is_active': True}
                serializer_staff = StaffSerializer(
                    data=staff_data, partial=True)
                serializer_staff.is_valid(raise_exception=True)
                serializer_staff.save()
                return Response({'success': 'Company Registration Successful'}, status=status.HTTP_201_CREATED)
        except:
            return Response({'error': 'An error occurred. Please try again!'}, status=status.HTTP_404_NOT_FOUND)


class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = User.objects.get(pk=request.user.pk)
            user_data = request.data.copy()
            response_data = {}
            if user_data.__contains__('name'):
                user.first_name = user_data['name']
                user.save()
            if user_data.__contains__('avatar'):
                old_avatar = UserProfile.objects.filter(user=user.id)
                if old_avatar.exists():
                    serializer = UserProfileSerializer(
                        old_avatar[0], data=request.data, partial=True)
                else:
                    request.data['user'] = user.id
                    serializer = UserProfileSerializer(
                        data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if serializer.data['avatar']:
                    response_data = {'avatar': serializer.data['avatar'].split(
                        '/media/')[1]} if serializer.data['avatar'].count('/media/') > 0 else {'avatar': serializer.data['avatar']}
            return Response({'success': 'Profile Updated!', **response_data}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Error!'}, status=status.HTTP_404_NOT_FOUND)


class UserContactCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserContact.objects.all()
    serializer_class = UserContactSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        request.data['user'] = user.pk
        if not UserContact.objects.filter(user=request.user, type='P').exists():
            request.data['type'] = 'P'
        return self.create(request)


class UserContactUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserContact.objects.all()
    serializer_class = UserContactSerializer

    def patch(self, request, pk):
        try:
            with transaction.atomic():
                if request.data.__contains__('type'):
                    old_contact1 = UserContact.objects.filter(
                        user=request.user, type='P')
                    if old_contact1.exists():
                        serializer1 = UserContactSerializer(
                            old_contact1[0], data={'type': 'S'}, partial=True)
                        serializer1.is_valid(raise_exception=True)
                        serializer1.save()
                old_contact = UserContact.objects.get(pk=pk, user=request.user)
                serializer = UserContactSerializer(
                    old_contact, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({'success': 'Contact updated!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'An error occured'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        UserContact.objects.filter(user=request.user, pk=pk).delete()
        return Response({'success': 'Contact deleted!'}, status=status.HTTP_200_OK)


class UserAddressCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserAddress.objects.all()
    serializer_class = UserAddressSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        request.data['user'] = user.pk
        if not UserAddress.objects.filter(user=request.user, type='P').exists():
            request.data['type'] = 'P'
        return self.create(request)


class UserAddressUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserAddress.objects.all()
    serializer_class = UserAddressSerializer

    def patch(self, request, pk):
        try:
            with transaction.atomic():
                if request.data.__contains__('type'):
                    old_contact1 = UserAddress.objects.filter(
                        user=request.user, type='P')
                    if old_contact1.exists():
                        serializer1 = UserAddressSerializer(
                            old_contact1[0], data={'type': 'S'}, partial=True)
                        serializer1.is_valid(raise_exception=True)
                        serializer1.save()
                old_contact = UserAddress.objects.get(pk=pk, user=request.user)
                serializer = UserAddressSerializer(
                    old_contact, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({'success': 'Address updated!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'An error occured'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        UserAddress.objects.filter(user=request.user, pk=pk).delete()
        return Response({'success': 'Address deleted!'}, status=status.HTTP_200_OK)


class UserGSTCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserGST.objects.all()
    serializer_class = UserGSTSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        request.data['user'] = user.pk
        if not UserGST.objects.filter(user=request.user, type='P').exists():
            request.data['type'] = 'P'
        return self.create(request)


class UserGSTUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserGST.objects.all()
    serializer_class = UserGSTSerializer

    def patch(self, request, pk):
        try:
            with transaction.atomic():
                if request.data.__contains__('type'):
                    old_gst1 = UserGST.objects.filter(
                        user=request.user, type='P')
                    if request.data['type'] == 'P' and old_gst1.exists():
                        serializer1 = UserGSTSerializer(
                            old_gst1[0], data={'type': 'S'}, partial=True)
                        serializer1.is_valid(raise_exception=True)
                        serializer1.save()
                old_gst = UserGST.objects.get(pk=pk, user=request.user)
                serializer = UserGSTSerializer(
                    old_gst, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({'success': 'GST updated!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'An error occured'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        UserGST.objects.filter(user=request.user, pk=pk).delete()
        return Response({'success': 'GST deleted!'}, status=status.HTTP_200_OK)


class UserCartCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserCart.objects.all()
    serializer_class = UserCartSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        request.data['user'] = user.pk
        cart_products = UserCart.objects.filter(user=user)
        product = cart_products.filter(product__id=request.data['product'])
        if product.exists():
            product = product[0]
            serializer = UserCartSerializer(
                product, data={'quantity': request.data['quantity']}, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': 'Cart updated!'}, status=status.HTTP_200_OK)
        return self.create(request)


class UserCartUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserCart.objects.all()
    serializer_class = UserCartSerializer

    def patch(self, request, pk):
        try:
            old_data = UserCart.objects.get(user=request.user, product__id=pk)
            serializer = UserCartSerializer(
                old_data, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': 'Cart updated!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'An error occured'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        item = UserCart.objects.filter(user=request.user, product__id=pk)
        if item.exists():
            item.delete()
        return Response({'success': 'Cart item deleted!'}, status=status.HTTP_200_OK)


class UserCartDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserCart.objects.all()
    serializer_class = UserCartSerializer

    def get(self, request, *args, **kwargs):
        UserCart.objects.filter(user=request.user).delete()
        return Response({'success': 'Cart deleted!'}, status=status.HTTP_200_OK)


class AdminLoginView(LoginView):
    def post(self, request):
        try:
            self.request = request
            self.serializer = self.get_serializer(data=self.request.data,
                                                  context={'request': request})
            self.serializer.is_valid(raise_exception=True)
            user = User.objects.get(username=self.serializer.data['username'])
            filter = (
                Q(status='R') & Q(members__member=user.id) & Q(members__is_active=True) & (
                    Q(members__role__code='AD') | Q(members__role__code='MA'))
            )
            if Company.objects.filter(filter).exists():
                super().login()
            else:
                msg = _('Unable to login with provided credentials.')
                return Response(data={'error': msg}, status=status.HTTP_404_NOT_FOUND)
            return super().get_response()
        except:
            return Response(data={'error': 'Login Failed!'}, status=status.HTTP_404_NOT_FOUND)


class StaffRoleGetView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = StaffRole.objects.all()
    serializer_class = StaffRoleSerializer


class OrderStatusGetView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer


class CategoryCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def post(self, request, *args, **kwargs):
        try:
            company = get_company_by_staff(self, request)
            request.data['company'] = company.id
            return self.create(request)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class CategoryUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def patch(self, request, pk):
        try:
            company = get_company_by_staff(self, request)
            old_category = Category.objects.get(id=pk, company=company)
            serializer = CategorySerializer(
                old_category, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(data={'error': 'An error occurred'}, status=status.HTTP_404_NOT_FOUND)


class CategoriesImportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        company = get_company_by_staff(self, request)
        data = request.data['dataToImport']
        id = 1
        try:
            with transaction.atomic():
                if request.data['deleteExistingData']:
                    Category.objects.filter(company=company).delete()
                for d in data:
                    d['company'] = company.id
                    if d['image'].strip() != '':
                        result = urllib.request.urlretrieve(d['image'])
                        file = File(open(result[0], "rb"), str(
                            time.time()).replace('.', '') + '.jpg')
                        d['image'] = file
                    else:
                        d.pop('image')
                    serializer = CategorySerializer(data=d, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    id += 1
                return Response({'success': 'Categories added'}, status=status.HTTP_201_CREATED)
        except:
            return Response({'error': 'Data Error at row '+str(id)}, status=status.HTTP_404_NOT_FOUND)


class CategoryGetView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request):
        company = get_company_by_staff(self, request)
        data = Category.objects.filter(
            company=company, name__icontains=request.query_params.get('search')).values()
        return Response(data=data, status=status.HTTP_200_OK)


class CategoryDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            company = get_company_by_staff(self, request)
            ids_to_delete = list(map(int, request.data['categoriesIds']))
            Category.objects.filter(
                company=company, id__in=ids_to_delete).delete()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        try:
            with transaction.atomic():
                company = get_company_by_staff(self, request)
                product_data = request.data
                image_data = []
                if product_data.__contains__('images'):
                    image_data = product_data.pop('images')
                tag_data = product_data.pop('tags')
                product_data['company'] = company.id
                serializer_product = ProductSerializer(
                    data=product_data, partial=True)
                serializer_product.is_valid(raise_exception=True)
                serializer_product.save()
                data_tags = [
                    {'product': serializer_product.data['id'], 'tag': int(tag)} for tag in tag_data]
                serializer_tag = ProductTagSerializer(
                    data=data_tags, many=True)
                serializer_tag.is_valid(raise_exception=True)
                serializer_tag.save()
                if len(image_data):
                    data_images = [
                        {'product': serializer_product.data['id'], 'image': img} for img in image_data]
                    serializer_image = ProductImageSerializer(
                        data=data_images, many=True)
                    serializer_image.is_valid(raise_exception=True)
                    serializer_image.save()
                return Response(status=status.HTTP_201_CREATED)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            with transaction.atomic():
                company = get_company_by_staff(self, request)
                image_data, tag_data = [], []
                product_data = request.data
                product_data._mutable = True
                if product_data.__contains__('is_active'):
                    isActive = product_data['is_active']
                    product_data['is_active'] = bool(isActive)
                else:
                    if product_data.__contains__('images'):
                        image_data = product_data.pop('images')
                    if product_data.__contains__('imagesToRemove'):
                        image_remove_data = product_data.pop('imagesToRemove')
                        ProductImage.objects.filter(
                            product=pk, id__in=image_remove_data).delete()
                    if product_data.__contains__('tags'):
                        tag_data = product_data.pop('tags')
                product_data._mutable = False
                old_product = Product.objects.get(id=pk, company=company)
                serializer_product = ProductSerializer(
                    old_product, data=product_data, partial=True)
                serializer_product.is_valid(raise_exception=True)
                serializer_product.save()
                if len(tag_data) > 0:
                    ProductTag.objects.filter(product=pk).delete()
                    data_tags = [
                        {'product': pk, 'tag': int(tag)} for tag in tag_data]
                    serializer_tag = ProductTagSerializer(
                        data=data_tags, many=True)
                    serializer_tag.is_valid(raise_exception=True)
                    serializer_tag.save()
                if len(image_data) > 0:
                    data_images = [{'product': pk, 'image': img}
                                   for img in image_data]
                    serializer_image = ProductImageSerializer(
                        data=data_images, many=True)
                    serializer_image.is_valid(raise_exception=True)
                    serializer_image.save()
                return Response(serializer_product.data, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductsImportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        company = get_company_by_staff(self, request)
        data = request.data['dataToImport']
        id = 1
        try:
            with transaction.atomic():
                if request.data['deleteExistingData']:
                    Product.objects.filter(company=company).delete()
                for d in data:
                    d['company'] = company.id
                    tag_data = d.pop('tags').split(',')

                    if d['image'].strip() != '':
                        result = urllib.request.urlretrieve(d['image'])
                        file = File(open(result[0], "rb"), str(
                            time.time()).replace('.', '') + '.jpg')
                        d['image'] = file
                    else:
                        d.pop('image')
                    serializer_product = ProductSerializer(
                        data=d, partial=True)
                    serializer_product.is_valid(raise_exception=True)
                    serializer_product.save()

                    data_tags = []
                    for tag in tag_data:
                        category = Category.objects.filter(Q(company=company) &
                                                           (Q(name__iexact=tag.strip()) | Q(slug__iexact=tag.strip())))
                        if category.exists():
                            data_tags.append(
                                {'product': serializer_product.data['id'], 'tag': int(category[0].id)})

                    serializer_tag = ProductTagSerializer(
                        data=data_tags, many=True)
                    serializer_tag.is_valid(raise_exception=True)
                    serializer_tag.save()
                    id += 1
                return Response({'success': 'Products added'}, status=status.HTTP_201_CREATED)
        except:
            return Response({'error': 'Data Error at row '+str(id)}, status=status.HTTP_404_NOT_FOUND)


class CouponCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def post(self, request, *args, **kwargs):
        company = get_company_by_staff(self, request)
        request.data['company'] = company.id
        if Coupon.objects.filter(company=company, code=request.data['code']).exists():
            return Response(data={'error': 'Discount code is already taken.'}, status=status.HTTP_404_NOT_FOUND)
        return self.create(request)


class CouponUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            company = get_company_by_staff(self, request)
            old_coupon = Coupon.objects.get(id=pk, company=company)
            serializer = CouponSerializer(
                old_coupon, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(data={'error': 'An error occurred'}, status=status.HTTP_404_NOT_FOUND)


class CouponDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            company = get_company_by_staff(self, request)
            ids_to_delete = list(map(int, request.data['couponsIds']))
            Coupon.objects.filter(
                company=company, id__in=ids_to_delete).delete()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class StaffCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                company = get_company_by_staff_admin(self, request)
                request.data['company'] = company.id
                users = User.objects.filter(
                    email=request.data['email'], is_active=True)
                if users.exists():
                    staffs = Staff.objects.filter(
                        company=company, member=users[0].id)
                    if not staffs.exists():
                        request.data['member'] = users[0].id
                        request.data.pop('email')
                        request.data['is_active'] = not settings.EMAIL_TASKS_REQUIRED
                        serializer = StaffSerializer(
                            data=request.data, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                    elif staffs.filter(is_active=True).exists():
                        return Response(data={'error': 'This user is already added.'}, status=status.HTTP_404_NOT_FOUND)
                    msg = 'Staff created successfully'
                    if settings.EMAIL_TASKS_REQUIRED:
                        send_email(users[0], 'SC', company)
                        msg = 'Email confirmation has been sent to the user'
                    return Response(data={'success': msg}, status=status.HTTP_201_CREATED)
                return Response(data={'error': 'User with this email either does not exists or is not verified.'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response(data={'error': 'Error Occurred!'}, status=status.HTTP_404_NOT_FOUND)


class StaffConfirmationEmailResponseView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request):
        try:
            with transaction.atomic():
                username = request.data['user']
                key = request.data['key']
                response = request.data['response']
                user = User.objects.get(username=username)
                email_token = EmailToken.objects.get(user=user, task='SC')
                if str(email_token.token) == str(key):
                    old_data = Staff.objects.get(member=user)
                    current_timestamp = str(int(time.time()))
                    ref = db.reference(
                        'notifications/'+str(old_data.company.id)+'/'+current_timestamp+'/')
                    if response == 'accept':
                        serializer = StaffSerializer(
                            old_data, data={'is_active': True}, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        ref.set({'category': 'staff', 'title': 'Staff Request Accepted',
                                'time': current_timestamp, 'message': 'User '+username+' accepted the request.'})
                    elif response == 'decline':
                        ref.set({'category': 'staff', 'title': 'Staff Request Declined',
                                'time': current_timestamp, 'message': 'User '+username+' declined the request.'})
                        old_data.delete()
                    else:
                        return Response(data={'error': 'Error Occurred!'}, status=status.HTTP_404_NOT_FOUND)
                    email_token.delete()
                    return Response(status=status.HTTP_200_OK)
                return Response(data={'error': 'Error Occurred!'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response(data={'error': 'Error Occurred!'}, status=status.HTTP_404_NOT_FOUND)


class StaffDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            company = get_company_by_staff_admin(self, request)
            ids_to_delete = list(map(int, request.data['staffsIds']))
            Staff.objects.filter(
                company=company, id__in=ids_to_delete).delete()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class StaffRoleUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    def patch(self, request, pk):
        try:
            company = get_company_by_staff_admin(self, request)
            old_data = Staff.objects.get(company=company, id=pk)
            serializer = StaffSerializer(
                old_data, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': 'Staff updated!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Error occured!'}, status=status.HTTP_404_NOT_FOUND)


class OrderCreateView(mixins.CreateModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                response_ids = []
                user = request.user
                customer_data = request.data['customerData']
                vendors = request.data['orderData']

                for key, value in vendors.items():
                    company = Company.objects.get(slug=key)
                    order_data = value
                    product_data = order_data.pop('products')
                    order_data['vendor'] = company.id
                    order_data['user'] = user.id
                    order_data['status'] = OrderStatus.objects.get(
                        code='PE').id
                    order_data['payment_method'] = PaymentMethod.objects.get(
                        code='COD').id
                    order_data = {**order_data, **customer_data}
                    serializer_order = OrderSerializer(
                        data=order_data, partial=True)
                    serializer_order.is_valid(raise_exception=True)
                    serializer_order.save()

                    data_products = []
                    for product in product_data:
                        p = Product.objects.get(
                            id=product['product'], company__slug=key)
                        f = File(open(p.thumbnail.path, 'rb'), str(
                            time.time()).replace('.', '') + '.jpg')
                        product = {'order': serializer_order.data['id'], 'name': p.name, 'description': p.description,
                                   'unit': p.unit, 'price': p.sale_price, 'quantity': product['quantity'], 'image': f}
                        data_products.append(product)
                    serializer_product = OrderProductSerializer(
                        data=data_products, many=True)
                    serializer_product.is_valid(raise_exception=True)
                    serializer_product.save()

                    response_ids.append(serializer_order.data['id'])

                    current_timestamp = str(int(time.time()))
                    ref = db.reference(
                        'notifications/'+str(company.id)+'/'+current_timestamp+'/')
                    ref.set({'category': 'order', 'title': 'Order Received', 'time': current_timestamp,
                            'message': 'Order #'+str(serializer_order.data['id'])+' has been received.'})

                if request.data['couponApplied']:
                    old_coupons = Coupon.objects.filter(
                        pk=int(request.data['couponApplied']))
                    if old_coupons.exists():
                        old_coupon = old_coupons[0]
                        serializer_coupon = CouponSerializer(old_coupon, data={'used': min(
                            old_coupon.used+1, old_coupon.total)}, partial=True)
                        serializer_coupon.is_valid(raise_exception=True)
                        serializer_coupon.save()

                return Response(data={'success': 'Order Saved!', 'ordersIds': response_ids}, status=status.HTTP_201_CREATED)
        except:
            return Response(data={'error': 'Error occurred!'}, status=status.HTTP_404_NOT_FOUND)


class OrderUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def patch(self, request, pk):
        try:
            company = get_company_by_staff(self, request)
            old_data = Order.objects.get(vendor=company, id=pk)
            serializer = OrderSerializer(
                old_data, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': 'Order updated!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Error occured!'}, status=status.HTTP_404_NOT_FOUND)


class ScannedImageCreateDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ScannedImage.objects.all()
    serializer_class = ScannedImageSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                type = request.data['type']
                image = request.data['image']
                old_data = ScannedImage.objects.filter(user=request.user)
                if old_data.exists():
                    serializer = ScannedImageSerializer(
                        old_data[0], data={'image': image}, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                else:
                    data = {'user': request.user.id, 'image': image}
                    serializer = ScannedImageSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                db.reference('qr-scan/' + str(request.user.id) + '/').delete()
                db.reference('qr-scan/' + str(request.user.id) + '/' +
                             type + '/').set({'url': serializer.data['image']})
                return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        db.reference('qr-scan/' + str(request.user.id) + '/').delete()
        ScannedImage.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_200_OK)
