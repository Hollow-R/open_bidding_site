from rest_framework import serializers
from .models import Auction

class AuctionSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Auction
        fields = ['id', 'title', 'description', 'starting_price', 'current_price', 'active', 'end_time', 'owner_name']