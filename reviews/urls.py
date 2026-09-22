from django.urls import path
from . import views

urlpatterns = [
    path('review/instructor/<int:booking_pk>/', views.submit_instructor_review, name='submit_instructor_review'),
    path('review/ski-center/<int:ski_center_pk>/', views.submit_ski_center_review, name='submit_ski_center_review'),
    path('review/rental/<int:reservation_pk>/', views.submit_rental_review, name='submit_rental_review'),
]