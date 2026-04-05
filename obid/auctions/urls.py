from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/tenders', views.AuctionViewSet) # API adresi: /auctions/api/tenders/

app_name = 'auctions'

urlpatterns = [
    path('', views.tender_list, name='list'), 
    path('', include(router.urls)),
    path('izlediklerim/', views.watchlist, name='watchlist'),
    path('<int:pk>/watchlist/toggle/', views.toggle_watchlist, name='toggle_watchlist'),
    path('<int:pk>/', views.tender_detail, name='detail'),
    path('create/', views.create_auction, name='create'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('notifications/read-all/', views.notifications_mark_all_read, name='notifications_read_all'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_read'),
    path('delete/<int:auction_id>/', views.delete_auction, name='delete'), 
    path('update/<int:auction_id>/', views.update_auction, name='update'),
    path('bid/delete/<int:bid_id>/', views.delete_bid, name='delete_bid'),
    path('file/image/<int:image_id>/delete/', views.delete_auction_image, name='delete_auction_image'),
    path('file/specification/<int:file_id>/delete/', views.delete_auction_specification, name='delete_auction_specification'),
]