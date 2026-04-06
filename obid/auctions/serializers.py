from rest_framework import serializers
from .models import Auction

class AuctionSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.username')
    winner_name = serializers.ReadOnlyField(source='winner.username')
    image_urls = serializers.SerializerMethodField()
    bids_count = serializers.IntegerField(source='bids.count', read_only=True)
    
    class Meta:
        model = Auction
        fields = [
            'id',
            'title',
            'description',
            'starting_price',
            'current_price',
            'active',
            'end_time',
            'owner_name',
            'winner_name',
            'image_urls',
            'bids_count',
        ]

    def get_image_urls(self, obj):
        return [image.image.url for image in obj.images.all()]