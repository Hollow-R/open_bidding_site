from decimal import Decimal, ROUND_CEILING

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Auction(models.Model):

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name = "auctions")
    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_auctions"
    )    

    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='auction_images/', blank=True, null=True, verbose_name="İhale Görseli")

    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def expire_if_needed(self):
        if self.active and self.end_time and timezone.now() > self.end_time:
            highest_bid = self.bids.order_by('-amount').first()
            self.winner = highest_bid.user if highest_bid else None
            self.active = False
            self.save(update_fields=['active', 'winner'])
            return True
        return False

    @classmethod
    def expire_overdue(cls):
        expired_auctions = cls.objects.filter(active=True, end_time__isnull=False, end_time__lt=timezone.now()).prefetch_related('bids')
        updated_count = 0
        for auction in expired_auctions:
            highest_bid = auction.bids.order_by('-amount').first()
            auction.winner = highest_bid.user if highest_bid else None
            auction.active = False
            auction.save(update_fields=['active', 'winner'])
            updated_count += 1
        return updated_count

    def get_minimum_bid_amount(self):
        minimum = self.current_price * Decimal('1.05')
        return minimum.quantize(Decimal('0.01'), rounding=ROUND_CEILING)

    class Meta:
        verbose_name = "İhale"
        verbose_name_plural = "İhaleler"

class Bid(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name = "bids"
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name = "bids"
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('auction', 'user', 'amount')
        verbose_name = "Teklif"
        verbose_name_plural = "Teklifler"

