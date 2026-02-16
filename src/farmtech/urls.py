"""
Farmtech URL configuration.
"""

from django.views.generic import TemplateView
from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from geonode.urls import urlpatterns

from farmtech.views import dataset, group, inference, auth, dashboard, queues


# Swagger/OpenAPI configuration
SchemaView = get_schema_view(
    openapi.Info(
        title="Farmtech API",
        default_version="v1",
        description="Documentazione API per il progetto Farmtech",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@farmtech.local"),
        license=openapi.License(name="GPL 3 License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path("research/", view=TemplateView.as_view(template_name="research.html")),
    path("inference/", view=TemplateView.as_view(template_name="inference.html")),
    path("uploader/", view=dataset.uploader_view, name="uploader"),
    # ------------ Swagger/OpenAPI endpoints ------------
    # re_path(
    #   r"^swagger(?P<format>\.json|\.yaml)$",
    #   SchemaView.without_ui(cache_timeout=0),
    #   name="schema-json",
    # ),
    # path(
    #   "swagger/",
    #   SchemaView.with_ui("swagger", cache_timeout=0),
    #   name="schema-swagger-ui",
    # ),
    # path("redoc/", SchemaView.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # ------------ Auth ------------
    path(
        "api/auth/keycloak/", auth.KeycloakAuthAPIView.as_view(), name="keycloak-auth"
    ),
    path(
        "api/auth/keycloak/register/",
        auth.KeycloakRegisterAPIView.as_view(),
        name="keycloak-register",
    ),
    path(
        "api/auth/keycloak/token-refresh/",
        auth.KeycloakTokenRefreshAPIView.as_view(),
        name="keycloak-token-refresh",
    ),
    path("auth/logout/", auth.KeycloakLogoutView.as_view(), name="farmtech-logout"),
    path(
        "account/logout/complete/",
        auth.KeycloakLogoutCompleteView.as_view(),
        name="logout-complete",
    ),
    # ------------ Group Profile ------------
    path(
        "api/group/group-join-request/",
        group.GroupJoinRequestAPIView.as_view(),
        name="group-join-request",
    ),
    path(
        "api/group/list/",
        group.GroupProfileListAPIView.as_view(),
        name="group-profile-list",
    ),
    #  ------------ Dataset & Inference ------------
    path(
        "api/dataset/update/",
        dataset.DatasetUpdateAPIView.as_view(),
        name="dataset-update",
    ),
    path(
        "api/dataset/excel-templates/",
        dataset.GroupExcelTemplatesAPIView.as_view(),
        name="dataset-excel-templates",
    ),
    path(
        "api/dataset/download-template/<int:dataset_experiment_id>",
        dataset.DownloadExcelTemplateAPIView.as_view(),
        name="dataset-download-template",
    ),
    path(
        "api/inference/trigger/",
        inference.RunSSHCommandView.as_view(),
        name="inference-trigger",
    ),
    # ------------ Dashboard ------------
    path(
        "api/dashboard/<int:pk>/publish/",
        dashboard.PublishDashboardAPIView.as_view(),
        name="dashboard-publish",
    ),
    # ------------ Queues ------------
    path(
        "api/queues/uploads-status/",
        queues.uploads_queue_status,
        name="uploads-queue-status",
    ),
]
