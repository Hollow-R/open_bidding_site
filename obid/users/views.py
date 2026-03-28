from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from auctions.models import Auction, Bid
import json
from django.core.serializers.json import DjangoJSONEncoder

# Register
def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Registration successful! Please login.")
        return redirect('login')

    return render(request, "users/register.html")


# Login
def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')

    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home_view(request):
    if request.user.is_superuser:
        auctions_list = list(Auction.objects.all().values(
            'id', 'title', "description", 'owner__username', 'current_price', "created_at", 'end_time', 'active'))
        
        bids_list = list(Bid.objects.all().values(
            'id', 'auction_id', 'user__username', 'amount', 'created_at'
        ))

        context = {
            'auctions_json': json.dumps(auctions_list, cls=DjangoJSONEncoder),
            'bids_json': json.dumps(bids_list, cls=DjangoJSONEncoder),
        }
        return render(request, 'users/admin_dashboard.html', context)
    else:
        auctions = Auction.objects.filter(active=True).order_by('-created_at')
        return render(request, 'users/dashboard.html', {'auctions': auctions})
