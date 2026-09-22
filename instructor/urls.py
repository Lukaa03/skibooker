from django.urls import path
from . import views

urlpatterns = [
    path('instructor/profil/', views.instructor_profile, name='instructor_profile'),
    path('instructor/<int:pk>/update/', views.update_instructor, name='update_instructor'),
    path('instructor/<int:pk>/add-slot/', views.add_time_slot, name='add_time_slot'),
    path('slot/<int:pk>/delete/', views.delete_time_slot, name='delete_time_slot'),
    path('booking/<int:pk>/accept/', views.accept_booking, name='accept_booking'),
    path('booking/<int:pk>/reject/', views.reject_booking, name='reject_booking'),
    path('booking/<int:pk>/complete/', views.complete_booking, name='complete_booking'),
    path('slot/<int:pk>/update/', views.update_time_slot, name='update_time_slot'),
    path('instructor/', views.instructors_list, name='instructors_list'),
    path('instructor/<int:pk>/', views.instructor_public_profile, name='instructor_public_profile'),
    path('slot/<int:slot_pk>/book/', views.book_slot, name='book_slot'),
]