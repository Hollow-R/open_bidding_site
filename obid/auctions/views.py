from django.shortcuts import render
from users.decorators import menu_permission_required
from rest_framework import viewsets
from .serializers import AuctionSerializer
from .models import Auction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import BidForm

class AuctionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Auction.objects.all().order_by('-created_at')
    serializer_class = AuctionSerializer

@menu_permission_required('auctions:list')
def tender_detail(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    
    if request.method == "POST":
        form = BidForm(request.POST, auction=auction)
        if form.is_valid():
            # Formdan gelen temiz veriyi al ama hemen kaydetme (user eklememiz lazım)
            bid = form.save(commit=False)
            bid.user = request.user
            bid.auction = auction
            bid.save() # Veritabanına Bid kaydı atıldı

            # İş kuralı: Auction fiyatını güncelle
            auction.current_price = bid.amount
            auction.save()

            messages.success(request, "Teklifiniz başarıyla kaydedildi.")
            return redirect('auctions:detail', pk=pk)
        else:
            # Form geçerli değilse (fiyat düşükse vb.) hataları mesaj olarak bas
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = BidForm(auction=auction)

    bids = auction.bids.all().order_by('-amount')[:5]
    return render(request, 'auctions/tender_detail.html', {
        'auction': auction, 
        'bids': bids, 
        'form': form
    })

@menu_permission_required('auctions:list')
def tender_list(request):
    return render(request, 'auctions/tender_list.html')
