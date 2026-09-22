from django.urls import path
from . import views

urlpatterns = [
    path('ski-center/profil/', views.ski_center_profile, name='ski_center_profile'),
    path('ski-center/<int:pk>/update/', views.update_ski_center, name='update_ski_center'),
    path('ski-center/<int:pk>/slope/add/', views.add_slope, name='add_slope'),
    path('ski-center/slope/<int:pk>/change/', views.change_slope_status, name='change_slope_status'),
    path('ski-center/slope/<int:pk>/delete/', views.delete_slope, name='delete_slope'),
    path('ski-center/<int:pk>/lift/add/', views.add_lift, name='add_lift'),
    path('ski-center/lift/<int:pk>/change/', views.change_lift_status, name='change_lift_status'),
    path('ski-center/lift/<int:pk>/delete/', views.delete_lift, name='delete_lift'),
    path('ski-center-public/<int:pk>/',views.ski_center_public_profile, name='ski_center_public_profile'),
    path('ski-centri/', views.ski_centri_lista, name='ski_centri_lista'),
    path('ski-centri/<int:pk>/', views.ski_center_public_profile, name='ski_centar_detalj'),
]