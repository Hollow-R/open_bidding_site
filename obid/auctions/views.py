from django.shortcuts import render
from users.decorators import menu_permission_required
from rest_framework import viewsets
from .serializers import AuctionSerializer
from .models import Auction, Bid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import BidForm, AuctionForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
import json
from django.http import JsonResponse


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

def create_auction(request):
    if request.method == "POST":
        form = AuctionForm(request.POST, request.FILES) # Resimler için request.FILES şart!
        if form.is_valid():
            auction = form.save(commit=False)
            auction.owner = request.user # İhaleyi sisteme giren kişi sahibi olur
            auction.current_price = auction.starting_price # Başlangıç fiyatı güncel fiyattır
            auction.save()
            return redirect('dashboard') # Başarılıysa dashboard'a dön
    else:
        form = AuctionForm()
    
    return render(request, 'auctions/create_auction.html', {'form': form})


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_auction(request, auction_id):
    try:
        auction = Auction.objects.get(id=auction_id)
        auction.delete()
        return JsonResponse({'success': True})
    except Auction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'İhale bulunamadı.'})
    

@user_passes_test(lambda u: u.is_superuser)
@require_POST
def update_auction(request, auction_id):
    try:
        auction = Auction.objects.get(id=auction_id)
        # JS'den gelen ham veriyi alıyoruz
        data = json.loads(request.body) 
        
        # Sadece gelen alanları güncelle (Mutlak Güç!)
        if 'title' in data: auction.title = data['title']
        if 'description' in data: auction.description = data['description']
        if 'active' in data: auction.active = data['active']
        if 'end_time' in data: auction.end_time = data['end_time']
        
        auction.save()
        return JsonResponse({'success': True})
    except Auction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'İhale bulunamadı.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_bid(request, bid_id):
    try:
        bid = Bid.objects.get(id=bid_id)
        auction = bid.auction
        bid.delete()

        highest_bid = auction.bids.order_by('-amount').first()
        if highest_bid:
            auction.current_price = highest_bid.amount
        else:
            auction.current_price = auction.starting_price
        auction.save()

        return JsonResponse({'success': True})
    except Bid.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bid bulunamadı.'})