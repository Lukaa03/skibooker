from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.home, name='home'),
    path('accounts/logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('accounts/login/', views.login_view, name = 'login'),
    path('klijent/profil/', views.client_profile, name='client_profile'),
    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('oprema/<int:pk>/otkazi/', views.cancel_equipment_reservation, name='cancel_equipment_reservation'),
    path('statistika/', views.admin_statistics, name='admin_statistics'),
    path('admin-panel/odobri/<int:pk>/', views.approve_request, name='approve_request'),
    path('admin-panel/odbij/<int:pk>/', views.reject_request, name='reject_request'),
]