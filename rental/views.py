from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Avg, Q

import ski_center
from accounts.models import ClientProfile, BusinessProfile
from ski_center.models import SkiCenterProfile
from .forms import EquipmentReservationForm, RejectReservationForm, EquipmentForm, EquipmentVariantForm
from .models import (
    Equipment,
    EquipmentReservation,
    EquipmentVariant, RentalProfile,
)


def rental_list(request):
    """
    Prikazuje listu svih rental firmi.

    Funkcionalnost:
        SSU04 - Pregled rental firmi.

    Parametri:
        request - HTTP zahtev.

    Povratna vrednost:
        Renderuje stranicu rental/rental_list.html sa
        listom svih registrovanih rental firmi i
        delom njihove ponude.
    """
    selected_center = request.GET.get('ski_center')

    rentals = (
        RentalProfile.objects
        .annotate(avg=Avg('reviews__rating', filter=Q(reviews__is_removed=False)))
        .select_related(
            'business_profile',
            'ski_center'
        )
        .prefetch_related(
            Prefetch(
                'equipment',
                queryset=Equipment.objects.filter(
                    is_active=True
                ).select_related('category', 'brand')
            )
        )
        .order_by('business_profile__business_name')
    )

    if selected_center:
        rentals = rentals.filter(
            ski_center_id=int(selected_center)
        )

    ski_centers = (
        SkiCenterProfile.objects
        .select_related(
            'business_profile'
        )
        .order_by(
            'business_profile__business_name'
        )
    )

    context = {
        'rentals': rentals,
        'ski_centers': ski_centers,
        'selected_center': selected_center
    }

    return render(
        request,
        'rental/rental_list.html',
        context
    )


def rentalPublicProfile(request, pk):
    """
    Prikazuje javni profil izabrane rental firme.

    Funkcionalnost:
        SSU04 - Pregled profila rental firme.

    Parametri:
        request - HTTP zahtev.
        pk - identifikator rental firme.

    Povratna vrednost:
        Renderuje stranicu rental/rentalPublicProfile.html sa
        podacima o izabranoj rental firmi.
    """

    rental = get_object_or_404(
        RentalProfile.objects.select_related(
            'business_profile',
            'ski_center'
        ),
        pk=pk
    )

    equipment = (
        Equipment.objects
        .filter(
            rental=rental,
            is_active=True
        )
        .select_related(
            'category',
            'brand'
        )
        .prefetch_related(
            'variants'
        )
    )

    reviews = rental.reviews.filter(is_removed=False).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    context = {
        'rental': rental,
        'equipment_list': equipment,
        'reviews': reviews,
        'avg_rating': avg_rating,
    }

    return render(
        request,
        'rental/rentalPublicProfile.html',
        context
    )

##brise se
def equipment_list(request, pk):
    """
        Prikazuje listu opreme izabrane rental firme.

        Funkcionalnost:
            SSU04 - Pregled opreme rental firme.

        Parametri:
            request - HTTP zahtev.
            pk - identifikator rental firme.

        Povratna vrednost:
            Renderuje stranicu rental/equipment_list.html sa
            listom dostupne opreme izabrane rental firme.
        """

    rental = get_object_or_404(
        RentalProfile.objects.select_related(
            'business_profile',
            'ski_center'
        ),
        pk=pk
    )

    equipment = (
        Equipment.objects
        .filter(
            rental=rental,
            is_active=True
        )
        .select_related(
            'category',
            'brand'
        )
    )

    context = {
        'rental': rental,
        'equipment': equipment
    }

    return render(
        request,
        'rental/equipment_list.html',
        context
    )


def equipment_detail(request, pk):
    """
    Prikazuje detalje izabranog modela opreme.

    Funkcionalnost:
        SSU04 - Pregled detalja opreme.

    Parametri:
        request - HTTP zahtev.
        pk - identifikator modela opreme.

    Povratna vrednost:
        Renderuje stranicu rental/equipment_detail.html.
    """

    equipment = get_object_or_404(
        Equipment.objects.select_related(
            'rental',
            'category',
            'brand'
        ),
        pk=pk,
        is_active=True
    )

    variants = EquipmentVariant.objects.filter(
        equipment=equipment,
        quantity__gt=0
    )

    form = EquipmentReservationForm()
    form.fields['equipment_variant'].queryset = variants

    context = {
        'equipment': equipment,
        'form': form
    }

    return render(
        request,
        'rental/equipment_detail.html',
        context
    )


@login_required
def reserve_equipment(request, pk):
    """
    Omogućava prijavljenom klijentu da rezerviše izabranu opremu.

    Prikazuje formu za izbor veličine, količine i perioda iznajmljivanja.
    Nakon uspešnog unosa kreira rezervaciju sa statusom 'ceka_potvrdu'.
    Pre kreiranja proverava da li izabrana varijanta pripada opremi i da li
    postoji dovoljna raspoloživa količina u traženom periodu.

    :model:`accounts.ClientProfile`
    :model:`rental.Equipment`
    :model:`rental.EquipmentVariant`
    :model:`rental.EquipmentReservation`
    :template:`rental/reserve_equipment.html`

    Argumenti: request - HTTP zahtev ulogovanog korisnika.
               pk - primarni ključ opreme koja se rezerviše.

    Return: Render reserve_equipment template sa formom ili redirect na
            detalje opreme nakon uspešno kreirane rezervacije.
    """

    equipment = get_object_or_404(
        Equipment.objects.select_related(
            'rental',
            'category',
            'brand'
        ),
        pk=pk,
        is_active=True
    )

    variants = EquipmentVariant.objects.filter(
        equipment=equipment,
        quantity__gt=0
    )

    reservation_error = None

    if request.method == 'POST':
        form = EquipmentReservationForm(
            request.POST
        )

        form.fields['equipment_variant'].queryset = variants

        if form.is_valid():

            if not hasattr(request.user, 'clientprofile'):
                reservation_error = (
                    'Samo klijentski nalog može rezervisati opremu.'
                )
            else:
                client = request.user.clientprofile

                reservation = form.save(commit=False)
                selected_variant = reservation.equipment_variant

                overlapping_reservations = (
                    EquipmentReservation.objects
                    .filter(
                        equipment_variant=selected_variant,
                        status__in=[
                            'ceka_potvrdu',
                            'potvrdjena'
                        ],
                        start_date__lte=reservation.end_date,
                        end_date__gte=reservation.start_date
                    )
                    .aggregate(
                        reserved_quantity=Sum('quantity')
                    )
                )

                reserved_quantity = (
                    overlapping_reservations['reserved_quantity']
                    or 0
                )

                available_quantity = (
                    selected_variant.quantity - reserved_quantity
                )

                if reservation.quantity > available_quantity:
                    form.add_error(
                        'quantity',
                        (
                            'Tražena količina nije dostupna u izabranom '
                            f'periodu. Dostupno je {available_quantity}.'
                        )
                    )
                else:
                    reservation.client = client
                    reservation.status = 'ceka_potvrdu'
                    print("USAO U SAVE")
                    reservation.save()
                    print("SACUVANA REZERVACIJA", reservation.pk)


                    return redirect(
                        'reservation_success',
                        reservation.pk
                    )
    else:
        form = EquipmentReservationForm()
        form.fields['equipment_variant'].queryset = variants

    context = {
        'equipment': equipment,
        'form': form,
        'reservation_error': reservation_error,
    }

    return render(
        request,
        'rental/equipment_detail.html',
        context
    )

@login_required
def reservation_success(request, pk):
    """
    Prikazuje stranicu uspešno poslate rezervacije.
    """

    reservation = get_object_or_404(
        EquipmentReservation.objects.select_related(
            'equipment_variant__equipment__brand',
            'equipment_variant__equipment__rental__business_profile'
        ),
        pk=pk,
        client=request.user.clientprofile
    )

    context = {
        'reservation': reservation
    }

    return render(
        request,
        'rental/reservation_success.html',
        context
    )


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render







@login_required
def rental_profile(request):
    """
    Prikazuje profil prijavljene rental firme.

    Funkcionalnost:
        SSU10 - Upravljanje opremom.
        SSU11 - Upravljanje rezervacijama.

    Parametri:
        request - HTTP zahtev prijavljenog korisnika.

    Povratna vrednost:
        Renderuje stranicu rental/rental_profile.html.
    """

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile.objects.select_related(
            'business_profile',
            'ski_center'
        ),
        business_profile=business
    )

    equipment = (
        Equipment.objects
        .filter(
            rental=rental,
            is_active=True
        )
        .select_related(
            'category',
            'brand'
        )
        .prefetch_related(
            'variants'
        )
    )

    reservations = (
        EquipmentReservation.objects
        .filter(
            equipment_variant__equipment__rental=rental
        )
        .select_related(
            'client__user',
            'equipment_variant__equipment__brand'
        )
    )

    context = {
        'rental': rental,
        'equipment': equipment,
        'reservations': reservations,
        'equipment_form': EquipmentForm(),
        'variant_form': EquipmentVariantForm(),
        'pending_reservations_count': reservations.filter(
            status='ceka_potvrdu'
        ).count(),
        "ski_centers": SkiCenterProfile.objects.all(),
    }


    return render(
        request,
        'rental/rental_profile.html',
        context
    )

@login_required
def update_rental_profile(request):

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    if request.method == "POST":

        business.business_name = request.POST.get(
            "business_name"
        )

        business.location = request.POST.get(
            "location"
        )

        business.save()

        rental.contact_email = request.POST.get(
            "contact_email"
        )

        rental.contact_phone = request.POST.get(
            "contact_phone"
        )

        rental.website = request.POST.get(
            "website"
        )

        rental.logo = request.POST.get(
            'logo',
            ''
        )

        rental.description = request.POST.get(
            "description"
        )

        rental.ski_center_id = (
            request.POST.get("ski_center")
            or None
        )

        rental.save()

        messages.success(
            request,
            "Podaci su uspešno sačuvani."
        )

    return redirect(
        f"{reverse('rental_profile')}?tab=profil"
    )


@login_required
def add_equipment(request):

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    if request.method == 'POST':

        form = EquipmentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            equipment = form.save(commit=False)
            equipment.rental = rental
            equipment.save()

            messages.success(
                request,
                'Oprema je uspešno dodata.'
            )

    return redirect(
        f"{reverse('rental_profile')}?tab=oprema"
    )


@login_required
def update_equipment(request, pk):

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    equipment = get_object_or_404(
        Equipment,
        pk=pk,
        rental=rental
    )

    if request.method == 'POST':

        form = EquipmentForm(
            request.POST,
            request.FILES,
            instance=equipment
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Oprema je uspešno izmenjena.'
            )

    return redirect(
        f"{reverse('rental_profile')}?tab=oprema"
    )


@login_required
def delete_equipment(request, pk):
    """
    Označava opremu kao neaktivnu.

    Funkcionalnost:
        SSU10 - Brisanje opreme.
    """

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    equipment = get_object_or_404(
        Equipment,
        pk=pk,
        rental=rental
    )

    if request.method == "POST":

        equipment.is_active = False
        equipment.save(
            update_fields=["is_active"]
        )

        messages.success(
            request,
            "Oprema je uspešno uklonjena iz ponude."
        )

    return redirect(
        f"{reverse('rental_profile')}?tab=oprema"
    )


@login_required
def add_variant(request, pk):

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    equipment = get_object_or_404(
        Equipment,
        pk=pk,
        rental=rental
    )

    if request.method == 'POST':

        form = EquipmentVariantForm(
            request.POST
        )

        if form.is_valid():

            variant = form.save(commit=False)

            existing = EquipmentVariant.objects.filter(
                equipment=equipment,
                size=variant.size
            ).first()

            if existing:

                existing.quantity += variant.quantity
                existing.save()

                messages.success(
                    request,
                    'Količina postojeće veličine je ažurirana.'
                )

            else:

                variant.equipment = equipment
                variant.save()

                messages.success(
                    request,
                    'Nova veličina je dodata.'
                )

    return redirect(
        f"{reverse('rental_profile')}?tab=oprema"
    )


@login_required
def accept_reservation(request, pk):
    """
    Omogućava rental firmi da prihvati zahtev za rezervaciju opreme.

    Funkcionalnost:
        SSU11 - Prihvatanje rezervacije opreme.
    """

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    reservation = get_object_or_404(
        EquipmentReservation.objects.select_related(
            'equipment_variant__equipment__rental'
        ),
        pk=pk,
        equipment_variant__equipment__rental=rental
    )

    if request.method != 'POST':
        return redirect('rental_profile')

    if reservation.status != 'ceka_potvrdu':
        messages.error(
            request,
            'Samo rezervacija koja čeka potvrdu može biti prihvaćena.'
        )
        return redirect('rental_profile')

    reservation.status = 'potvrdjena'
    reservation.reject_reason = None
    reservation.save(
        update_fields=[
            'status',
            'reject_reason'
        ]
    )

    messages.success(
        request,
        'Rezervacija je uspešno prihvaćena.'
    )

    return redirect('rental_profile')


@login_required
def reject_reservation(request, pk):

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    reservation = get_object_or_404(
        EquipmentReservation,
        pk=pk,
        equipment_variant__equipment__rental=rental
    )

    if request.method != 'POST':
        return redirect('rental_profile')

    if reservation.status != 'ceka_potvrdu':
        messages.error(
            request,
            'Rezervaciju nije moguće odbiti.'
        )
        return redirect('rental_profile')

    reservation.status = 'odbijena'
    reservation.reject_reason = request.POST.get(
        'reject_reason'
    )

    reservation.save(
        update_fields=[
            'status',
            'reject_reason'
        ]
    )

    messages.success(
        request,
        'Rezervacija je odbijena.'
    )

    return redirect('rental_profile')


@login_required
def complete_reservation(request, pk):
    """
    Omogućava rental firmi da potvrđenu rezervaciju označi
    kao realizovanu.

    Funkcionalnost:
        SSU11 - Evidentiranje realizovanog iznajmljivanja.
    """

    business = get_object_or_404(
        BusinessProfile,
        user=request.user,
        business_type='rental'
    )

    rental = get_object_or_404(
        RentalProfile,
        business_profile=business
    )

    reservation = get_object_or_404(
        EquipmentReservation.objects.select_related(
            'equipment_variant__equipment__rental'
        ),
        pk=pk,
        equipment_variant__equipment__rental=rental
    )

    if request.method != 'POST':
        return redirect('rental_profile')

    if reservation.status != 'potvrdjena':
        messages.error(
            request,
            'Samo potvrđena rezervacija može biti označena kao realizovana.'
        )
        return redirect('rental_profile')

    reservation.status = 'realizovana'
    reservation.save(
        update_fields=['status']
    )

    messages.success(
        request,
        'Rezervacija je označena kao realizovana.'
    )

    return redirect('rental_profile')