from django.urls import path
from .views import *

app_name = 'authentication'

urlpatterns = [
    # Endpoint di test per Keycloak
    path('test/keycloak-health/', keycloak_health_check, name='keycloak_health_check'),
    path('test/protected/', protected_endpoint, name='protected_endpoint'),
    path('test/validate-token/', validate_token, name='validate_token'),
    path('test/config/', keycloak_config, name='keycloak_config'),
    
    # Endpoint di autenticazione
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('validate-jwt/', validate_jwt_token, name='validate_jwt_token'),
]