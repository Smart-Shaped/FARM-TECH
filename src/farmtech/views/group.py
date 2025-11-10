import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from geonode.groups.models import GroupProfile, GroupMember
from farmtech.models import RoleChangeRequest
from farmtech.serializers import GroupJoinRequestSerializer
from django.db import transaction
from farmtech.authentication import KeycloakAuthentication
from geonode.geoapps.models import GeoApp

logger = logging.getLogger(__name__)

class GroupJoinRequestAPIView(APIView):
    """
    API per richiedere l'iscrizione ad un Group Profile.
    
    Invia una email a tutti i manager del group profile richiesto con le informazioni
    dell'utente, il ruolo desiderato e le motivazioni della richiesta.
    
    Parametri richiesti:
    - group_profile_id: ID del GroupProfile a cui si vuole accedere
    - requested_role: Ruolo richiesto ('manager' o 'member')
    - motivation: Motivazione della richiesta (può essere un testo lungo)
    
    L'utente che fa la richiesta viene automaticamente recuperato dal token di autenticazione.
    """
    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GroupJoinRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Dati non validi", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group_profile_id = serializer.validated_data['group_profile_id']
        requested_role = serializer.validated_data['requested_role']
        motivation = serializer.validated_data['motivation']
        user = request.user
        
        try:
            # Verifica che il group profile esista
            try:
                group_profile = GroupProfile.objects.get(id=group_profile_id)
            except GroupProfile.DoesNotExist:
                return Response(
                    {"error": f"GroupProfile con ID {group_profile_id} non trovato"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verifica se l'utente è già membro del gruppo
            existing_membership = GroupMember.objects.filter(
                group=group_profile,
                user=user
            ).first()
            
            if existing_membership:
                return Response(
                    {
                        "error": "Sei già membro di questo gruppo",
                        "current_role": existing_membership.role
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Recupera tutti i manager del group profile
            managers = GroupMember.objects.filter(
                group=group_profile,
                role='manager'
            ).select_related('user')
            
            if not managers.exists():
                logger.warning(
                    f"Nessun manager trovato per il GroupProfile {group_profile.title} (ID: {group_profile_id})"
                )
                return Response(
                    {
                        "error": "Nessun manager trovato per questo gruppo. Contatta l'amministratore del sistema."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Prepara il contenuto dell'email
            role_label = "Manager" if requested_role == "manager" else "Membro"
            subject = f"Nuova richiesta di iscrizione al gruppo '{group_profile.title}'"
            
            message = f"""
                        Ciao,

                        L'utente {user.get_full_name() or user.username} (Email: {user.email}) ha richiesto l'iscrizione al gruppo '{group_profile.title}'.

                        Dettagli della richiesta:
                        - Nome utente: {user.username}
                        - Nome completo: {user.get_full_name() or 'Non specificato'}
                        - Email: {user.email}
                        - Ruolo richiesto: {role_label}

                        Motivazione:
                        {motivation}

                        Per approvare o gestire questa richiesta, accedi al pannello di amministrazione di Farmtech.

                        ---
                        Questa è una email automatica generata dal sistema Farmtech.
                        """.strip()
                                    
            # Lista delle email dei manager
            manager_emails = [
                manager.user.email 
                for manager in managers 
                if manager.user.email
            ]
            
            if not manager_emails:
                logger.warning(
                    f"Nessun manager con email valida trovato per il GroupProfile {group_profile.title}"
                )
                return Response(
                    {
                        "error": "Nessun manager con email valida trovato per questo gruppo. Contatta l'amministratore del sistema."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Salva la richiesta nel database e invia le email in una transazione
            with transaction.atomic():
                # Crea il record della richiesta
                role_request = RoleChangeRequest.objects.create(
                    user=user,
                    group_profile=group_profile,
                    group_role=requested_role,
                    motivazione=motivation
                )
                
                # Invia l'email a tutti i manager
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=manager_emails,
                    fail_silently=False,
                )
            
            logger.info(
                f"Richiesta di iscrizione inviata con successo. "
                f"Utente: {user.username}, Gruppo: {group_profile.title}, "
                f"Ruolo: {requested_role}, Manager notificati: {len(manager_emails)}"
            )
            
            return Response({
                "success": True,
                "message": "Richiesta di iscrizione inviata con successo",
                "details": {
                    "group_profile": group_profile.title,
                    "requested_role": role_label,
                    "managers_notified": len(manager_emails),
                    "request_id": role_request.id
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Errore nell'invio della richiesta di iscrizione: {str(e)}",
                exc_info=True
            )
            return Response(
                {"error": f"Errore nell'elaborazione della richiesta: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GroupProfileListAPIView(APIView):
    """
    API per ottenere la lista di tutti i GroupProfile esistenti.
    
    Restituisce informazioni basilari su tutti i gruppi disponibili nel sistema,
    inclusi ID, titolo, descrizione, slug e livello di accesso.
    
    Non richiede autenticazione per permettere agli utenti di vedere i gruppi disponibili.
    """
    permission_classes = []  # Nessuna autenticazione richiesta
    
    def get(self, request):
        try:
            # Recupera tutti i GroupProfile ordinati per titolo
            group_profiles = GroupProfile.objects.all().order_by('title')
            
            # Prepara i dati da restituire
            groups_data = []
            for group in group_profiles:
                # Conta il numero di membri totali
                total_members = GroupMember.objects.filter(group=group).count()
                
                # Conta il numero di manager
                total_managers = GroupMember.objects.filter(
                    group=group,
                    role='manager'
                ).count()
                
                dashboard = GeoApp.objects.filter(group=group.group, is_published=True).first()

                groups_data.append({
                    'id': group.id,
                    'title': group.title,
                    'slug': group.slug,
                    'description': group.description or '',
                    'access': group.access,  # 'public', 'public-invite', 'private'
                    'email': group.email or '',
                    'logo': group.logo.url if group.logo else None,
                    'members_count': total_members,
                    'managers_count': total_managers,
                    'created': group.created.isoformat() if group.created else None,
                    'last_modified': group.last_modified.isoformat() if group.last_modified else None,
                    'dashboard_id': dashboard.id if dashboard else None,
                })
            
            logger.info(f"Lista di {len(groups_data)} GroupProfile restituita con successo")
            
            return Response({
                'success': True,
                'count': len(groups_data),
                'groups': groups_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Errore nel recupero dei GroupProfile: {str(e)}",
                exc_info=True
            )
            return Response(
                {"error": f"Errore nel recupero dei gruppi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
