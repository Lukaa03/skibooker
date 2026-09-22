from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import ClientProfile
from instructor.models import Booking
from ski_center.models import SkiCenterProfile
from .models import Review
from .forms import ReviewForm
from rental.models import EquipmentReservation

@login_required
def submit_instructor_review(request, booking_pk):
    client = get_object_or_404(ClientProfile, user=request.user)
    booking = get_object_or_404(Booking, pk=booking_pk, client=client)

    if booking.status != 'realizovana':
        messages.error(request, "Možete oceniti samo realizovan čas.")
    elif Review.objects.filter(booking=booking).exists():
        messages.error(request, "Već ste ostavili recenziju za ovu rezervaciju.")

    else:
        if request.method == 'POST':
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.reviewer = client
                review.instructor = booking.time_slot.instructor
                review.booking = booking
                review.save()
                messages.success(request, "Vaša recenzija je uspešno objavljena.")

    return redirect('client_profile')

@login_required
def submit_ski_center_review(request, ski_center_pk):
    client = get_object_or_404(ClientProfile, user=request.user)
    ski_center = get_object_or_404(SkiCenterProfile, pk=ski_center_pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = client
            review.ski_center = ski_center
            review.save()
            messages.success(request, "Vaša recenzija je uspešno objavljena.")

    return redirect('ski_center_public_profile', pk=ski_center.pk)

@login_required
def submit_rental_review(request, reservation_pk):
    client = get_object_or_404(ClientProfile, user=request.user)
    reservation = get_object_or_404(EquipmentReservation, pk=reservation_pk, client=client)

    if reservation.status != 'realizovana':
        messages.error(request, "Možete oceniti samo realizovanu rezervaciju.")
    elif Review.objects.filter(reservation=reservation).exists():
        messages.error(request, "Već ste ostavili recenziju za ovu rezervaciju.")
    else:
        if request.method == 'POST':
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.reviewer = client
                review.rental = reservation.equipment_variant.equipment.rental
                review.reservation = reservation
                review.save()
                messages.success(request, "Vaša recenzija je uspešno objavljena.")

    return redirect('client_profile')