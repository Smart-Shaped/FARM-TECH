from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # Campi per integrazione Keycloak
    keycloak_id = models.UUIDField(unique=True, null=True, blank=True, 
                                   help_text="ID utente in Keycloak")
    keycloak_username = models.CharField(max_length=150, null=True, blank=True,
                                        help_text="Username in Keycloak")
    
    # Metadati di sincronizzazione
    last_keycloak_sync = models.DateTimeField(null=True, blank=True,
                                             help_text="Ultima sincronizzazione con Keycloak")
    keycloak_roles = models.JSONField(default=list, blank=True,
                                     help_text="Ruoli dell'utente in Keycloak")
    
    # Campi aggiuntivi
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['keycloak_id']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_keycloak_role(self, role_name):
        """
        Verifica se l'utente ha un ruolo specifico in Keycloak
        """
        return role_name in self.keycloak_roles
    
    def update_from_keycloak(self, keycloak_data):
        self.first_name = keycloak_data.get('given_name', self.first_name)
        self.last_name = keycloak_data.get('family_name', self.last_name)
        self.email = keycloak_data.get('email', self.email)
        self.keycloak_username = keycloak_data.get('preferred_username', self.keycloak_username)
        
        # Aggiorna ruoli se presenti
        if 'realm_access' in keycloak_data:
            self.keycloak_roles = keycloak_data['realm_access'].get('roles', [])
        
        self.last_keycloak_sync = timezone.now()
        self.save()