from pathlib import Path

from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from auctions.models import Auction, Bid
from users.models import Menu, GroupMenuPermission
from django.http import JsonResponse
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from .decorators import menu_permission_required, user_has_menu_permission

def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('users:register')
        user = User.objects.create_user(username=username, email=email, password=password)
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


@menu_permission_required("users:user_management")
def user_management_view(request):
    return redirect(f"{reverse('users:dashboard')}?section=users")


@menu_permission_required("users:group_permissions")
def group_permissions_view(request):
    return redirect(f"{reverse('users:dashboard')}?section=groups")

@login_required
def home_view(request):
    can_view_system_panel = user_has_menu_permission(request.user, 'users:admin_dashboard')
    can_view_public_dashboard = user_has_menu_permission(request.user, 'users:dashboard')
    can_view_auctions = user_has_menu_permission(request.user, 'auctions:list')
    can_view_user_management = user_has_menu_permission(request.user, 'users:user_management')
    can_view_group_permissions = user_has_menu_permission(request.user, 'users:group_permissions')

    if can_view_system_panel:
        Auction.expire_overdue()
        auctions_list = []
        bids_list = []
        if can_view_auctions:
            auctions_qs = (
                Auction.objects.select_related('owner', 'winner')
                .prefetch_related('images', 'specification_files')
                .all()
            )
            for a in auctions_qs:
                gallery_images = [{'id': img.id, 'url': img.image.url} for img in a.images.all()]
                specification_files = [
                    {
                        'id': sf.id,
                        'url': sf.file.url,
                        'name': Path(sf.file.name).name if sf.file.name else 'dosya.pdf',
                    }
                    for sf in a.specification_files.all()
                ]
                auctions_list.append({
                    'id': a.id,
                    'title': a.title,
                    'description': a.description,
                    'owner__username': a.owner.username if a.owner_id else '',
                    'current_price': a.current_price,
                    'winner__username': a.winner.username if a.winner_id else None,
                    'created_at': a.created_at,
                    'end_time': a.end_time,
                    'active': a.active,
                    'gallery_images': gallery_images,
                    'specification_files': specification_files,
                })
            bids_list = list(Bid.objects.all().values('id', 'auction_id', 'user__username', 'amount', 'created_at'))

        users_list = []
        user_groups_list = []

        if can_view_user_management or can_view_group_permissions:
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

        if can_view_group_permissions:
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
            'can_view_auctions': can_view_auctions,
        }

        return render(request, 'users/admin_dashboard.html', context)
    elif can_view_public_dashboard:
        # Normal kullanıcı (Aktif İhaleler)
        Auction.expire_overdue()
        auctions = Auction.objects.filter(active=True)

        q = request.GET.get('q', '').strip()
        if q:
            auctions = auctions.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )

        min_start = request.GET.get('min_starting_price')
        if min_start:
            try:
                auctions = auctions.filter(starting_price__gte=min_start)
            except ValueError:
                pass

        max_start = request.GET.get('max_starting_price')
        if max_start:
            try:
                auctions = auctions.filter(starting_price__lte=max_start)
            except ValueError:
                pass

        min_current = request.GET.get('min_current_price')
        if min_current:
            try:
                auctions = auctions.filter(current_price__gte=min_current)
            except ValueError:
                pass

        max_current = request.GET.get('max_current_price')
        if max_current:
            try:
                auctions = auctions.filter(current_price__lte=max_current)
            except ValueError:
                pass

        sort_by = request.GET.get('sort_by', '-created_at')
        valid_sorts = {
            '-created_at': '-created_at',  # En son açılan
            'created_at': 'created_at',    # En eski açılan
            'current_price': 'current_price',  # En düşük fiyat
            '-current_price': '-current_price', # En yüksek fiyat
        }
        if sort_by not in valid_sorts:
            sort_by = '-created_at'
        
        auctions = auctions.order_by(sort_by).prefetch_related('images')
        return render(request, 'users/dashboard.html', {
            'auctions': auctions,
            'search_query': q,
            'min_starting_price': min_start,
            'max_starting_price': max_start,
            'min_current_price': min_current,
            'max_current_price': max_current,
            'sort_by': sort_by,
        })
    else:
        # İzin yok - hata mesajı göster
        return render(request, 'users/dashboard.html', {
            'permission_error': True,
        })


# --- GRUP İŞLEMLERİ ---
@menu_permission_required("users:group_permissions")
@require_POST
def add_group(request):
    data = json.loads(request.body)
    group = Group.objects.create(name=data.get('name'))
    return JsonResponse({'success': True, 'id': group.id})


@menu_permission_required("users:user_management")
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

@menu_permission_required("users:user_management")
@require_POST
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Kullanıcı bulunamadı.'})

    user.delete()
    return JsonResponse({'success': True})

@menu_permission_required("users:group_permissions")
@require_POST
def update_group(request, obj_id):
    data = json.loads(request.body)
    Group.objects.filter(id=obj_id).update(name=data.get('name'))
    return JsonResponse({'success': True})

@menu_permission_required("users:group_permissions")
@require_POST
def delete_group(request, obj_id):
    Group.objects.filter(id=obj_id).delete()
    return JsonResponse({'success': True})

# --- YETKİ İŞLEMLERİ ---
@menu_permission_required("users:group_permissions")
@require_POST
def add_perm(request):
    data = json.loads(request.body)
    perm = GroupMenuPermission.objects.create(
        group_id=data.get('group_id'),
        menu_id=data.get('menu_id'),
        can_view=data.get('can_view', True)
    )
    return JsonResponse({'success': True, 'id': perm.id})

@menu_permission_required("users:group_permissions")
@require_POST
def update_perm(request, obj_id):
    data = json.loads(request.body)
    perm = GroupMenuPermission.objects.get(id=obj_id)
    if 'menu_id' in data: perm.menu_id = data['menu_id']
    if 'can_view' in data: perm.can_view = data['can_view']
    perm.save()
    return JsonResponse({'success': True})

@menu_permission_required("users:group_permissions")
@require_POST
def delete_perm(request, obj_id):
    GroupMenuPermission.objects.filter(id=obj_id).delete()
    return JsonResponse({'success': True})
