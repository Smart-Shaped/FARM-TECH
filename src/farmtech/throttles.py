from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class FiveDaysRegisteredThrottleRate(UserRateThrottle):
    rate = '5/day'

class IPBasedThrottle(AnonRateThrottle):
    rate = '20/hour'
    
    def get_cache_key(self, request, view):
        """
        Usa l'IP come chiave di cache anche per utenti autenticati
        """
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
