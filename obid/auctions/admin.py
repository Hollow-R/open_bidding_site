from django.contrib import admin
from .models import Auction, AuctionImage, AuctionSpecificationFile, AuctionWinNotification, Bid


class AuctionImageInline(admin.TabularInline):
    model = AuctionImage
    extra = 0


class AuctionSpecificationFileInline(admin.TabularInline):
    model = AuctionSpecificationFile
    extra = 0


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'starting_price', 'current_price', 'vat_rate', 'active', 'end_time')
    list_filter = ('active', 'owner', 'vat_rate')
    search_fields = ('title', 'description')
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'description', 'owner', 'winner')
        }),
        ('Fiyat Bilgileri (Net)', {
            'fields': ('starting_price', 'current_price', 'vat_rate'),
            'description': 'Fiyatlar KDV hariç (net) olarak girilir. KDV oranı varsayılan olarak %18 dir.'
        }),
        ('Durum', {
            'fields': ('active', 'created_at', 'end_time')
        }),
    )
    inlines = (AuctionImageInline, AuctionSpecificationFileInline)
    readonly_fields = ('created_at',)

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'user', 'amount', 'created_at')
    list_filter = ('auction', 'user')


@admin.register(AuctionWinNotification)
class AuctionWinNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'auction', 'amount', 'read_at', 'created_at')
    list_filter = ('read_at',)
    search_fields = ('user__username', 'auction__title')
    raw_id_fields = ('user', 'auction')