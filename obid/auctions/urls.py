from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/tenders', views.AuctionViewSet) # API adresi: /auctions/api/tenders/

app_name = 'auctions'

urlpatterns = [
    path('', views.tender_list, name='list'), 
    path('', include(router.urls)),
    path('<int:pk>/', views.tender_detail, name='detail'),
    path('create/', views.create_auction, name='create'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('delete/<int:auction_id>/', views.delete_auction, name='delete'), 
    path('update/<int:auction_id>/', views.update_auction, name='update'),
    path('bid/delete/<int:bid_id>/', views.delete_bid, name='delete_bid'),
]