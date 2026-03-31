from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('', views.home_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('', views.home_view, name='admin_dashboard'),

    path('api/group/add/', views.add_group, name='add_group'),
    path('api/group/update/<int:obj_id>/', views.update_group, name='update_group'),
    path('api/group/delete/<int:obj_id>/', views.delete_group, name='delete_group'),
    path('api/user/update/<int:user_id>/', views.update_user, name='update_user'),
    path('api/user/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    path('api/perm/add/', views.add_perm, name='add_perm'),
    path('api/perm/update/<int:obj_id>/', views.update_perm, name='update_perm'),
    path('api/perm/delete/<int:obj_id>/', views.delete_perm, name='delete_perm'),
]