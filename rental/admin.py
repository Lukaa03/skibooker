from django.contrib import admin

from .models import (
    RentalProfile,
    EquipmentCategory,
    Brand,
    Equipment,
    EquipmentVariant,
    EquipmentReservation
)


@admin.register(RentalProfile)
class RentalProfileAdmin(admin.ModelAdmin):
    list_display = (
        'business_profile',
        'ski_center',
        'average_rating'
    )

    search_fields = (
        'business_profile__business_name',
    )


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )

    search_fields = (
        'name',
    )


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )

    search_fields = (
        'name',
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'brand',
        'model',
        'category',
        'rental',
        'price_per_day',
        'is_active'
    )

    list_filter = (
        'category',
        'brand',
        'is_active'
    )

    search_fields = (
        'model',
        'brand__name'
    )


@admin.register(EquipmentVariant)
class EquipmentVariantAdmin(admin.ModelAdmin):
    list_display = (
        'equipment',
        'size',
        'quantity'
    )

    list_filter = (
        'equipment__category',
    )


@admin.register(EquipmentReservation)
class EquipmentReservationAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'equipment_variant',
        'quantity',
        'start_date',
        'end_date',
        'status'
    )

    list_filter = (
        'status',
    )

    search_fields = (
        'client__user__first_name',
        'client__user__last_name'
    )