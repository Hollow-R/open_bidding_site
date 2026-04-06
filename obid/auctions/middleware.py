from django.core.cache import cache
from django.utils import timezone
from .models import Auction


class AuctionExpirationMiddleware:
    """Expire overdue auctions during request handling.

    This middleware runs on incoming requests but only performs the expiration
    check at most once per minute to avoid excessive DB load.
    """

    CACHE_KEY = "auctions.expire_overdue.last_run"
    INTERVAL_SECONDS = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.maybe_expire_auctions()
        response = self.get_response(request)
        return response

    def maybe_expire_auctions(self):
        last_run = cache.get(self.CACHE_KEY)
        now = timezone.now()
        if last_run is None or (now - last_run).total_seconds() >= self.INTERVAL_SECONDS:
            if cache.add(self.CACHE_KEY, now, self.INTERVAL_SECONDS):
                Auction.expire_overdue()
