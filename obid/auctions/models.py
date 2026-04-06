from decimal import Decimal, ROUND_CEILING

from django.core.validators import FileExtensionValidator
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

    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.18'), help_text="KDV oranı (örn: 0.18 için %18)")

    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def _close_auction(self):
        highest_bid = self.bids.order_by('-amount').first()
        self.winner = highest_bid.user if highest_bid else None
        self.active = False
        self.save(update_fields=['active', 'winner'])
        notify_auction_winner(self)

    def expire_if_needed(self):
        if self.active and self.end_time and timezone.now() > self.end_time:
            self._close_auction()
            return True
        return False

    @classmethod
    def expire_overdue(cls):
        expired_auctions = cls.objects.filter(active=True, end_time__isnull=False, end_time__lt=timezone.now()).prefetch_related('bids')
        updated_count = 0
        for auction in expired_auctions:
            auction._close_auction()
            updated_count += 1
        return updated_count

    def get_minimum_bid_amount(self):
        minimum = self.current_price * Decimal('1.05')
        return minimum.quantize(Decimal('0.01'), rounding=ROUND_CEILING)

    @property
    def starting_price_with_vat(self):
        """Net başlangıç fiyatı + KDV"""
        return (self.starting_price * (1 + self.vat_rate)).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

    @property
    def current_price_with_vat(self):
        """Mevcut fiyat + KDV"""
        return (self.current_price * (1 + self.vat_rate)).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

    class Meta:
        verbose_name = "İhale"
        verbose_name_plural = "İhaleler"


class AuctionImage(models.Model):
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="auction_gallery/")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "İhale görseli"
        verbose_name_plural = "İhale görselleri"


class AuctionSpecificationFile(models.Model):
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name="specification_files",
    )
    file = models.FileField(
        upload_to="auction_specifications/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Şartname (PDF)"
        verbose_name_plural = "Şartname dosyaları"


class AuctionWatchlistEntry(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="auction_watchlist_entries",
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name="watchlist_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        unique_together = ("user", "auction")
        verbose_name = "İzleme listesi kaydı"
        verbose_name_plural = "İzleme listesi kayıtları"


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


class AuctionWinNotification(models.Model):
    """İhale kazanıldığında kullanıcıya gösterilen bildirim."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="auction_win_notifications",
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name="win_notifications",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "auction"],
                name="unique_auction_win_notification_per_user_auction",
            )
        ]
        verbose_name = "Kazanım bildirimi"
        verbose_name_plural = "Kazanım bildirimleri"


def notify_auction_winner(auction):
    """İhale kapandıktan ve kazanan atandıktan sonra tek sefer bildirim oluşturur."""
    if not auction.winner_id:
        return
    AuctionWinNotification.objects.get_or_create(
        user_id=auction.winner_id,
        auction=auction,
        defaults={"amount": auction.current_price},
    )

