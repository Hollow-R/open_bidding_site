from pathlib import Path

from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets
from .serializers import AuctionSerializer
from .models import (
    Auction,
    AuctionImage,
    AuctionSpecificationFile,
    AuctionWatchlistEntry,
    AuctionWinNotification,
    Bid,
    notify_auction_winner,
)
from django.contrib import messages
from .forms import BidForm, AuctionForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from users.decorators import menu_permission_required
import json
from django.http import JsonResponse

MAX_AUCTION_IMAGES = 10
MAX_SPECIFICATION_PDFS = 5
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _file_suffix(name):
    return Path(name).suffix.lower()


def _validate_auction_uploads(image_files, pdf_files):
    errors = []
    if len(image_files) > MAX_AUCTION_IMAGES:
        errors.append(f"En fazla {MAX_AUCTION_IMAGES} görsel yükleyebilirsiniz.")
    for f in image_files:
        if _file_suffix(f.name) not in ALLOWED_IMAGE_SUFFIXES:
            errors.append(f"Desteklenmeyen görsel (JPEG, PNG, GIF, WebP): {f.name}")
    if len(pdf_files) > MAX_SPECIFICATION_PDFS:
        errors.append(f"En fazla {MAX_SPECIFICATION_PDFS} şartname PDF’i yükleyebilirsiniz.")
    for f in pdf_files:
        if _file_suffix(f.name) != ".pdf":
            errors.append(f"Şartname yalnızca PDF olmalıdır: {f.name}")
    return errors


class AuctionViewSet(viewsets.ReadOnlyModelViewSet): #Router için lazım
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer

    def get_queryset(self):
        Auction.expire_overdue()
        return Auction.objects.all().order_by('-created_at')


def tender_detail(request, pk):
    auction = get_object_or_404(
        Auction.objects.prefetch_related("images", "specification_files"),
        pk=pk,
    )
    auction.expire_if_needed()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.warning(request, "Teklif vermek için önce giriş yapmalısınız.")
            return redirect('auctions:detail', pk=pk)
        form = BidForm(request.POST, auction=auction)
        if not auction.active:
            messages.error(request, "Bu ihale bitmiş olduğu için artık teklif kabul etmiyor.")
        elif form.is_valid():

            bid = form.save(commit=False)
            bid.user = request.user
            bid.auction = auction
            bid.save() # Veritabanına Bid kaydı atıldı

            auction.current_price = bid.amount
            auction.save()

            messages.success(request, "Teklifiniz başarıyla kaydedildi.")
            return redirect('auctions:detail', pk=pk)
        else:
            # Form geçerli değilse (fiyat düşükse vb.) hataları mesaj olarak bas
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = BidForm(auction=auction) if request.user.is_authenticated else None

    bids = auction.bids.all().order_by('-amount')[:5]
    min_next_bid = auction.get_minimum_bid_amount()
    is_watched = False
    if request.user.is_authenticated:
        is_watched = AuctionWatchlistEntry.objects.filter(
            user=request.user, auction=auction
        ).exists()
    return render(request, 'auctions/tender_detail.html', {
        'auction': auction,
        'bids': bids,
        'form': form,
        'min_next_bid': min_next_bid,
        'is_watched': is_watched,
    })

def tender_list(request):
    return render(request, 'auctions/tender_list.html')

@menu_permission_required("auctions:create")
def create_auction(request):
    if request.method == "POST":
        form = AuctionForm(request.POST, request.FILES)
        image_files = [f for f in request.FILES.getlist("images") if f.name]
        pdf_files = [f for f in request.FILES.getlist("specifications") if f.name]
        upload_errors = _validate_auction_uploads(image_files, pdf_files)
        for err in upload_errors:
            messages.error(request, err)
        if form.is_valid() and not upload_errors:
            auction = form.save(commit=False)
            auction.owner = request.user # İhaleyi sisteme giren kişi sahibi olur
            auction.current_price = auction.starting_price # Başlangıç fiyatı güncel fiyattır
            auction.save()
            for i, img in enumerate(image_files):
                AuctionImage.objects.create(auction=auction, image=img, order=i)
            for i, pdf in enumerate(pdf_files):
                AuctionSpecificationFile.objects.create(auction=auction, file=pdf, order=i)
            return redirect('users:dashboard') # Başarılıysa dashboard'a dön
    else:
        form = AuctionForm()
    
    return render(request, 'auctions/create_auction.html', {'form': form})

@login_required 
def my_bids(request):
    user_bids = (
        Bid.objects.filter(user=request.user)
        .select_related("auction")
        .order_by("-created_at", "-id")
    )
    return render(request, 'auctions/my_bids.html', {'bids': user_bids})


@login_required
def watchlist(request):
    entries = (
        AuctionWatchlistEntry.objects.filter(user=request.user)
        .select_related("auction")
        .prefetch_related("auction__images")
        .order_by("-created_at", "-id")
    )
    auctions = [e.auction for e in entries]
    return render(request, "auctions/watchlist.html", {"auctions": auctions})


@login_required
@require_POST
def toggle_watchlist(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    entry, created = AuctionWatchlistEntry.objects.get_or_create(
        user=request.user, auction=auction
    )
    if not created:
        entry.delete()
        watched = False
    else:
        watched = True
    return JsonResponse({"success": True, "watched": watched})


@menu_permission_required("auctions:management")
@require_POST
def delete_auction(request, auction_id):
    try:
        auction = Auction.objects.get(id=auction_id)
        auction.delete()
        return JsonResponse({'success': True})
    except Auction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'İhale bulunamadı.'})
    

@menu_permission_required("auctions:management")
@require_POST
def update_auction(request, auction_id):
    try:
        auction = Auction.objects.get(id=auction_id)
        data = json.loads(request.body)

        was_active = auction.active

        if 'title' in data:
            auction.title = data['title']
        if 'description' in data:
            auction.description = data['description']
        if 'active' in data:
            auction.active = data['active']
        if 'end_time' in data:
            auction.end_time = data['end_time']

        # Manuel kapatmada kazananı en yüksek tekliften ata ve bildirim oluştur
        if was_active and not auction.active:
            highest_bid = auction.bids.order_by('-amount').first()
            auction.winner = highest_bid.user if highest_bid else None
            auction.save()
            notify_auction_winner(auction)
        else:
            auction.save()

        return JsonResponse({'success': True})
    except Auction.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'İhale bulunamadı.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@menu_permission_required("auctions:management")
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


@menu_permission_required("auctions:management")
@require_POST
def delete_auction_image(request, image_id):
    try:
        img = AuctionImage.objects.get(pk=image_id)
        img.image.delete(save=False)
        img.delete()
        return JsonResponse({'success': True})
    except AuctionImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Görsel bulunamadı.'})


@menu_permission_required("auctions:management")
@require_POST
def delete_auction_specification(request, file_id):
    try:
        spec = AuctionSpecificationFile.objects.get(pk=file_id)
        spec.file.delete(save=False)
        spec.delete()
        return JsonResponse({'success': True})
    except AuctionSpecificationFile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Şartname dosyası bulunamadı.'})


@login_required
@require_POST
def notification_mark_read(request, pk):
    updated = AuctionWinNotification.objects.filter(
        pk=pk,
        user=request.user,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    return JsonResponse({'success': True, 'marked': bool(updated)})


@login_required
@require_POST
def notifications_mark_all_read(request):
    AuctionWinNotification.objects.filter(
        user=request.user,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    return JsonResponse({'success': True})

