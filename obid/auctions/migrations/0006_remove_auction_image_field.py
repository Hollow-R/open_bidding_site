# Generated manually — drop legacy single-image field on Auction

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0005_auction_gallery_and_specifications'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='auction',
            name='image',
        ),
    ]
