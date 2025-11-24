"""
Custom throttling classes for FarmTech app.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class FiveDaysRegisteredThrottleRate(UserRateThrottle):
    """
    Rate limit for all authenticated users.
    Applies to ALL users, including staff and superusers.
    """

    rate = "5/day"

    def allow_request(self, request, view):
        """
        Override to apply throttling to staff/superusers as well.
        Removes the bypass for staff/superuser that exists in SimpleRateThrottle.
        """
        if request.user and request.user.is_authenticated:
            self.key = self.get_cache_key(request, view)
            if self.key is None:
                return True

            self.history = self.cache.get(self.key, [])
            self.now = self.timer()

            while self.history and self.history[-1] <= self.now - self.duration:
                self.history.pop()

            if len(self.history) >= self.num_requests:
                return self.throttle_failure()

            return self.throttle_success()

        return True


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
        Removes the bypass for staff/superuser that exists in SimpleRateThrottle.
        """
        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()

        return self.throttle_success()
