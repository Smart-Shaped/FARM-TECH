"""
Custom throttling classes for FarmTech app.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class FiveDaysRegisteredThrottleRate(UserRateThrottle):
    """
    Rate limit for users registered in the last 5 days.
    """

    rate = "5/day"


class IPBasedThrottle(AnonRateThrottle):
    """
    Rate limit based on IP address.
    """

    rate = "20/hour"

    def get_cache_key(self, request, view):
        """
        Usa l'IP come chiave di cache anche per utenti autenticati
        """
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
