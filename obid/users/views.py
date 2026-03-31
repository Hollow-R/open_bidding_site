from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from auctions.models import Auction, Bid
from users.models import Menu, GroupMenuPermission
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
import json
from django.core.serializers.json import DjangoJSONEncoder


def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('users:register')
        user = User.objects.create_user(username=username, email=email, password=password)
        customer_group, created = Group.objects.get_or_create(name="Müşteri")
        user.groups.add(customer_group)
        user.save()
        messages.success(request, "Registration successful! Please login.")
        return redirect('users:login')

    return render(request, "users/register.html")


# Login
def login_view(request):
    # Eğer kullanıcı zaten giriş yapmışsa ana sayfaya gönder
    if request.user.is_authenticated:
        return redirect('users:dashboard')

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('users:dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('users:login')

    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    return redirect('users:login')

@login_required
def home_view(request):
    if user_in_group(request.user, "Admin"):
        # Süresi geçen ihaleleri devre dışı bırak
        Auction.expire_overdue()

        # Admin verileri...
        auctions_list = list(Auction.objects.all().values('id', 'title', "description", 'owner__username', 'current_price', 'winner__username', "created_at", 'end_time', 'active'))
        bids_list = list(Bid.objects.all().values('id', 'auction_id', 'user__username', 'amount', 'created_at'))
        users_list = []
        user_groups_list = []
        for user in User.objects.prefetch_related('groups').all():
            group_ids = list(user.groups.values_list('id', flat=True))
            group_names = ', '.join(user.groups.values_list('name', flat=True))
            users_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined,
                'group_names': group_names
            })
            user_groups_list.append({
                'user_id': user.id,
                'group_ids': group_ids,
                'group_names': group_names
            })
        groups_list = list(Group.objects.all().values('id', 'name'))
        menus_list = list(Menu.objects.filter(is_active=True).values('id', 'title', 'parent_menu__title'))
        perms_list = list(GroupMenuPermission.objects.all().values('id', 'group_id', 'menu_id', 'can_view'))

        context = {
            'auctions_json': json.dumps(auctions_list, cls=DjangoJSONEncoder),
            'bids_json': json.dumps(bids_list, cls=DjangoJSONEncoder),
            'users_json': json.dumps(users_list, cls=DjangoJSONEncoder),
            'user_groups_json': json.dumps(user_groups_list, cls=DjangoJSONEncoder),
            'groups_json': json.dumps(groups_list, cls=DjangoJSONEncoder),
            'menus_json': json.dumps(menus_list, cls=DjangoJSONEncoder),
            'perms_json': json.dumps(perms_list, cls=DjangoJSONEncoder),
        }
        return render(request, 'users/admin_dashboard.html', context)
    
    elif user_in_group(request.user, "İhale Yöneticisi"):
        Auction.expire_overdue()
        auctions_list = list(Auction.objects.all().values('id', 'title', "description", 'owner__username', 'current_price', 'winner__username', "created_at", 'end_time', 'active'))
        bids_list = list(Bid.objects.all().values('id', 'auction_id', 'user__username', 'amount', 'created_at'))

        context = {
            'auctions_json': json.dumps(auctions_list, cls=DjangoJSONEncoder),
            'bids_json': json.dumps(bids_list, cls=DjangoJSONEncoder),
        }

        return render(request, 'users/admin_dashboard.html', context)
    else:
        # Normal kullanıcı (Aktif İhaleler)
        Auction.expire_overdue()
        auctions = Auction.objects.filter(active=True).order_by('-created_at')
        return render(request, 'users/dashboard.html', {'auctions': auctions})
    

# --- GRUP İŞLEMLERİ ---
@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def add_group(request):
    data = json.loads(request.body)
    group = Group.objects.create(name=data.get('name'))
    return JsonResponse({'success': True, 'id': group.id})


@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def update_user(request, user_id):
    data = json.loads(request.body)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Kullanıcı bulunamadı.'})

    if 'username' in data:
        username = data.get('username', '').strip()
        if username and username != user.username:
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Bu kullanıcı adı zaten kullanımda.'})
            user.username = username
    if 'email' in data:
        user.email = data.get('email')
    if 'is_active' in data:
        user.is_active = data.get('is_active')
    if 'is_staff' in data:
        user.is_staff = data.get('is_staff')
    if 'is_superuser' in data:
        user.is_superuser = data.get('is_superuser')
    user.save()

    if 'group_ids' in data:
        group_ids = data.get('group_ids') or []
        user.groups.set(group_ids)

    return JsonResponse({'success': True})

@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Kullanıcı bulunamadı.'})

    user.delete()
    return JsonResponse({'success': True})

@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def update_group(request, obj_id):
    data = json.loads(request.body)
    Group.objects.filter(id=obj_id).update(name=data.get('name'))
    return JsonResponse({'success': True})

@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def delete_group(request, obj_id):
    Group.objects.filter(id=obj_id).delete()
    return JsonResponse({'success': True})

# --- YETKİ İŞLEMLERİ ---
@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def add_perm(request):
    data = json.loads(request.body)
    perm = GroupMenuPermission.objects.create(
        group_id=data.get('group_id'),
        menu_id=data.get('menu_id'),
        can_view=data.get('can_view', True)
    )
    return JsonResponse({'success': True, 'id': perm.id})

@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def update_perm(request, obj_id):
    data = json.loads(request.body)
    perm = GroupMenuPermission.objects.get(id=obj_id)
    if 'menu_id' in data: perm.menu_id = data['menu_id']
    if 'can_view' in data: perm.can_view = data['can_view']
    perm.save()
    return JsonResponse({'success': True})

@user_passes_test(lambda u: u.groups.filter(name="Admin").exists())
@require_POST
def delete_perm(request, obj_id):
    GroupMenuPermission.objects.filter(id=obj_id).delete()
    return JsonResponse({'success': True})
