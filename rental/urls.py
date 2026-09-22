from django.urls import path

from . import views


urlpatterns = [


    path(
        'rental/',
        views.rental_list,
        name='rental_list'
    ),
    path(
        'rental/<int:pk>/',
        views.rentalPublicProfile,
        name='rentalPublicProfile'
    ),

    path(
        'equipment/<int:pk>/',
        views.equipment_detail,
        name='equipment_detail'
    ),

    path(
        'equipment/<int:pk>/reserve/',
        views.reserve_equipment,
        name='reserve_equipment'
    ),

    path(
        'reservation/<int:pk>/success/',
        views.reservation_success,
        name='reservation_success'
    ),

    path(
        'rental/profile/',
        views.rental_profile,
        name='rental_profile'
    ),

    path(
        "rental/profile/update/",
        views.update_rental_profile,
        name="update_rental_profile",
    ),

    path(
        'rental/profile/equipment/add/',
        views.add_equipment,
        name='add_equipment'
    ),

    path(
        'equipment/<int:pk>/update/',
        views.update_equipment,
        name='update_equipment'
    ),

    path(
        'equipment/<int:pk>/delete/',
        views.delete_equipment,
        name='delete_equipment'
    ),

    path(
        'equipment/<int:pk>/variant/add/',
        views.add_variant,
        name='add_variant'
    ),


    path(
        'reservation/<int:pk>/accept/',
        views.accept_reservation,
        name='accept_reservation'
    ),

    path(
        'reservation/<int:pk>/reject/',
        views.reject_reservation,
        name='reject_reservation'
    ),

    path(
        'reservation/<int:pk>/complete/',
        views.complete_reservation,
        name='complete_reservation'
    ),
]