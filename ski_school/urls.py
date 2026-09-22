from django.urls import path
from . import views

urlpatterns = [
    path('ski-school/profil/', views.ski_school_profile, name='ski_school_profile'),
]