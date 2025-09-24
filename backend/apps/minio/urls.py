from django.urls import path, re_path
from .views import MinIOTokenView, MinIOProxyView

app_name = 'minio'

urlpatterns = [
    path('token/', MinIOTokenView.as_view(), name='minio_token'),
    re_path(r'^proxy/(?P<path>.*)$', MinIOProxyView.as_view(), name='minio_proxy'),
]