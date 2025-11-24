"""
Custom throttling classes for FarmTech app.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class FiveDaysRegisteredThrottleRate(UserRateThrottle):
    """
    Rate limit for users registered in the last 5 days.
    Applies to ALL users, including staff and superusers.
    """

    rate = "5/day"

    def allow_request(self, request, view):
        """
        Override to apply throttling to staff/superusers as well.
        """
        # Always check throttle, even for staff/superusers
        return super(UserRateThrottle, self).allow_request(request, view)


class IPBasedThrottle(AnonRateThrottle):
    """
    Rate limit based on IP address.
    Applies to ALL requests, including from staff and superusers.
    """

    rate = "20/hour"

    def get_cache_key(self, request, view):
        """
        Usa l'IP come chiave di cache anche per utenti autenticati
        """
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def allow_request(self, request, view):
        """
        Override to apply throttling to staff/superusers as well.
        """
        # Always check throttle, even for staff/superusers
        return super(AnonRateThrottle, self).allow_request(request, view)
