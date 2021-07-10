from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from graphqlapi.customerschema import schema_with_auth, schema_without_auth
from graphqlapi.adminschema import schema

def graphql_token_view():
    view = GraphQLView.as_view(schema=schema_with_auth)
    view = permission_classes((IsAuthenticated,))(view)
    view = authentication_classes((TokenAuthentication,))(view)
    view = api_view(['GET', 'POST'])(view)
    return view

def graphql_admin_token_view():
    view = GraphQLView.as_view(schema=schema)
    view = permission_classes((IsAuthenticated,))(view)
    view = authentication_classes((TokenAuthentication,))(view)
    view = api_view(['GET', 'POST'])(view)
    return view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('rest-auth/', include('rest_auth.urls')),
    path('graphql_admin/', graphql_admin_token_view()),
    path('graphql_with_auth/', graphql_token_view()),
    path('graphql_without_auth/', csrf_exempt(GraphQLView.as_view(schema=schema_without_auth))),
    path('graphiql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema_with_auth))),
    path('restapi/', include('restapi.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)