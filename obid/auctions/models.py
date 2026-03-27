from django.db import models
from django.contrib.auth.models import User

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

