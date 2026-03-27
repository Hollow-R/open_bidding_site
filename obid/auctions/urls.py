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
]