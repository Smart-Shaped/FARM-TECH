from django.urls import path
from .views import *
from .views.role_views import (
    viewer_content,
    editor_content,
    admin_content,
    admin_or_editor_content,
    user_profile,
    check_permissions,
    public_info,
    ViewerOnlyAPIView,
    EditorOnlyAPIView,
    AdminOnlyAPIView,
    DynamicRoleAPIView,
    CustomRoleAPIView
)
from .views.role_management_views import (
    get_available_roles,
    get_user_roles,
    assign_role_to_user,
    remove_role_from_user,
    set_user_roles,
    list_users_with_roles,
    sync_user_roles_from_keycloak
)

app_name = 'authentication'

urlpatterns = [
    # Endpoint di test per Keycloak
    path('test/keycloak-health/', keycloak_health_check, name='keycloak_health_check'),
    path('test/protected/', protected_endpoint, name='protected_endpoint'),
    path('test/config/', keycloak_config, name='keycloak_config'),
    
    # Endpoint di autenticazione
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('validate-jwt/', validate_jwt_token, name='validate_jwt_token'),
    
    # Endpoint per la gestione dei ruoli - Function-based views
    path('roles/viewer/', viewer_content, name='viewer_content'),
    path('roles/editor/', editor_content, name='editor_content'),
    path('roles/admin/', admin_content, name='admin_content'),
    path('roles/admin-or-editor/', admin_or_editor_content, name='admin_or_editor_content'),
    path('roles/profile/', user_profile, name='user_profile'),
    path('roles/check-permissions/', check_permissions, name='check_permissions'),
    path('roles/info/', public_info, name='public_role_info'),
    
    # Endpoint per la gestione dei ruoli - Class-based views
    path('roles/class-based/viewer/', ViewerOnlyAPIView.as_view(), name='viewer_cbv'),
    path('roles/class-based/editor/', EditorOnlyAPIView.as_view(), name='editor_cbv'),
    path('roles/class-based/admin/', AdminOnlyAPIView.as_view(), name='admin_cbv'),
    path('roles/class-based/dynamic/', DynamicRoleAPIView.as_view(), name='dynamic_role_cbv'),
    path('roles/class-based/custom/', CustomRoleAPIView.as_view(), name='custom_role_cbv'),
    
    # Endpoint per la gestione amministrativa dei ruoli (solo admin)
    path('admin/roles/available/', get_available_roles, name='get_available_roles'),
    path('admin/roles/user/<int:user_id>/', get_user_roles, name='get_user_roles'),
    path('admin/roles/assign/', assign_role_to_user, name='assign_role_to_user'),
    path('admin/roles/remove/', remove_role_from_user, name='remove_role_from_user'),
    path('admin/roles/set/', set_user_roles, name='set_user_roles'),
    path('admin/roles/users/', list_users_with_roles, name='list_users_with_roles'),
    path('admin/roles/sync/', sync_user_roles_from_keycloak, name='sync_user_roles'),
]
