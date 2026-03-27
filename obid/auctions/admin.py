from django.contrib import admin
from .models import Auction, Bid

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'starting_price', 'current_price', 'active', 'end_time')
    list_filter = ('active', 'owner')
    search_fields = ('title', 'description')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'user', 'amount', 'created_at')
    list_filter = ('auction', 'user')