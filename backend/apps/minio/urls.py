from django.urls import path, re_path
from apps.minio.views.keycloak_integration import MinIOTokenView, MinIOProxyView
from apps.minio.views.data_management import minio_webhook

app_name = 'minio'

urlpatterns = [
    path('token/', MinIOTokenView.as_view(), name='minio_token'),
    re_path(r'^proxy/(?P<path>.*)$', MinIOProxyView.as_view(), name='minio_proxy'),
    path('webhook/', minio_webhook, name='minio_webhook'),
]