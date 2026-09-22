from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import BusinessProfile
from instructor.models import InstructorProfile
from .models import SkiCenterProfile, Slope, Lift
from reviews.models import Review
from rental.models import RentalProfile, EquipmentReservation

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q
from ski_center.models import SkiCenterProfile
import requests

def get_coordinates(location):
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': location, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'SkiBooker/1.0'},
            timeout=5
        )
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lng = float(data[0]['lon'])
            if 40 < lat < 47 and 13 < lng < 24:
                return lat, lng
    except Exception:
        pass
    return None, None


def ski_centri_lista(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '')

    ski_centri = SkiCenterProfile.objects.select_related(
        'business_profile'
    ).prefetch_related('slopes', 'lifts', 'ski_schools').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )

    if q:
        ski_centri = ski_centri.filter(
            Q(business_profile__business_name__icontains=q) |
            Q(business_profile__location__icontains=q) |
            Q(description__icontains=q)
        )

    if sort == 'naziv_asc':
        ski_centri = ski_centri.order_by('business_profile__business_name')
    elif sort == 'naziv_desc':
        ski_centri = ski_centri.order_by('-business_profile__business_name')
    elif sort == 'ocena_desc':
        ski_centri = ski_centri.order_by('-avg_rating')
    elif sort == 'ocena_asc':
        ski_centri = ski_centri.order_by('avg_rating')
    else:
        ski_centri = ski_centri.order_by('business_profile__business_name')

    return render(request, 'ski_center/skiCentersList.html', {
        'ski_centri': ski_centri,
    })



@login_required
def ski_center_profile(request):
    """
    Prikazuje profil ulogovanog ski centra sa stazama, žičarama i instruktorima.

    :model:`ski_center.SkiCenterProfile`
    :model:`ski_center.Slope`
    :model:`ski_center.Lift`
    :model:`instructor.InstructorProfile`
    :template:`ski_center/skiCenterProfile.html`

    Argumenti:  request - HTTP zahtev ulogovanog ski centra.

    Return: Render skiCenterProfile template sa stazama, žičarama i instruktorima.
    """
    bp = get_object_or_404(BusinessProfile, user = request.user)
    ski_center = get_object_or_404(SkiCenterProfile, business_profile=bp)
    slopes = Slope.objects.filter(ski_center=ski_center)
    lifts = Lift.objects.filter(ski_center=ski_center)
    instructors = InstructorProfile.objects.filter(ski_center=ski_center)
    reviews = ski_center.reviews.filter(is_removed=False).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    rentals = RentalProfile.objects.filter(ski_center=ski_center)
    bookings_count = EquipmentReservation.objects.filter(
        equipment_variant__equipment__rental__ski_center=ski_center
    ).count()

    return render(request, 'ski_center/skiCenterProfile.html', {
        'ski_center': ski_center, 'slopes': slopes, 'lifts': lifts, 'instructors': instructors,
        'slopes_count': slopes.count(), 'lifts_count': lifts.count(), 'instructors_count': instructors.count(),
        'rentals_count': rentals.count(),
        'bookings_count': bookings_count,
        'avg_rating': avg_rating,
        'reviews': reviews,
    })

@login_required
def update_ski_center(request, pk):
    """
    Ažurira kontakt podatke i opis ski centra.

    :model:`ski_center.SkiCenterProfile`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ ski centra.

    Return: Redirect na ski_center_profile sa success porukom.
    """
    ski_center = get_object_or_404(SkiCenterProfile, pk=pk)
    if request.method == 'POST':
        ski_center.contact_email = request.POST.get('contact_email')
        ski_center.contact_phone = request.POST.get('contact_phone')
        ski_center.website = request.POST.get('website')
        ski_center.description = request.POST.get('description')
        if 'photo' in request.FILES:
            ski_center.photo = request.FILES['photo']
        ski_center.save()
        ski_center.business_profile.business_name = request.POST.get('business_name')
        ski_center.business_profile.location = request.POST.get('location')
        ski_center.business_profile.save()

        post_lat = request.POST.get('latitude')
        post_lng = request.POST.get('longitude')
        if post_lat and post_lng:
            ski_center.latitude = post_lat
            ski_center.longitude = post_lng
            ski_center.save()
            messages.success(request, 'Profil je uspešno ažuriran.')
        else:
            lat, lng = get_coordinates(ski_center.business_profile.location)
            if lat and lng:
                ski_center.latitude = lat
                ski_center.longitude = lng
                ski_center.save()
                messages.success(request, 'Profil je uspešno ažuriran.')
            else:
                ski_center.latitude = None
                ski_center.longitude = None
                ski_center.save()
                messages.warning(request,'Profil je sačuvan, ali lokacija nije prepoznata — centar neće biti prikazan na mapi.')

    return redirect('ski_center_profile')


@login_required
def add_slope(request, pk):
    """
    Dodaje novu stazu ski centru.

    :model:`ski_center.Slope`

    Argumenti:  request - HTTP zahtev. (mora biti POST metoda)
                pk - Primarni ključ ski centra.

    Return: Redirect na ski_center_profile sa success porukom.
    """
    ski_center = get_object_or_404(SkiCenterProfile, pk=pk)
    if request.method == 'POST':
        Slope.objects.create(
            ski_center=ski_center,
            name=request.POST.get('name'),
            length_km=request.POST.get('length_km'),
            difficulty=request.POST.get('difficulty'),
            status=request.POST.get('status', 'otvorena')
        )
        messages.success(request, 'Staza je dodata.')
    return redirect('ski_center_profile')


@login_required
def change_slope_status(request, pk):
    """
    Menja status staze između otvorena/zatvorena.

    :model:`ski_center.Slope`

    Argumenti:  request - HTTP zahtev. (mora biti POST metoda)
                pk - Primarni ključ staze.

    Return: Redirect na ski_center_profile.
    """
    slope = get_object_or_404(Slope, pk=pk)
    if request.method == 'POST':
        if slope.status == 'otvorena':
            slope.status = 'zatvorena'
        else:
            slope.status = 'otvorena'
        slope.save()
    return redirect('ski_center_profile')


@login_required
def delete_slope(request, pk):
    """
    Briše stazu iz ski centra.

    :model:`ski_center.Slope`

     Argumenti:  request - HTTP zahtev. (mora biti POST metoda)
                pk - Primarni ključ staze.

    Return: Redirect na ski_center_profile sa success porukom.
    """
    slope = get_object_or_404(Slope, pk=pk)
    if request.method == 'POST':
        slope.delete()
        messages.success(request, 'Staza je obrisana.')
    return redirect('ski_center_profile')

@login_required
def add_lift(request, pk):
    """
    Dodaje novu žičaru ski centru.

    :model:`ski_center.Lift`

    Argumenti:  request - HTTP zahtev. (mora biti POST metoda)
                pk - Primarni ključ ski centra.

    Return: Redirect na ski_center_profile sa success porukom.
    """
    ski_center = get_object_or_404(SkiCenterProfile, pk=pk)
    if request.method == 'POST':
        Lift.objects.create(
            ski_center=ski_center,
            name=request.POST.get('name'),
            status='aktivna',
        )
        messages.success(request, 'Žičara je dodata.')
    return redirect('ski_center_profile')


@login_required
def change_lift_status(request, pk):
    """
    Menja status žičare između aktivna/neaktivna.

    :model:`ski_center.Lift`

    Argumenti:  request - HTTP zahtev. (mora biti POST metoda)
                pk - Primarni ključ  žičare.

    Return: Redirect na ski_center_profile.
    """
    lift = get_object_or_404(Lift, pk=pk)
    if request.method == 'POST':
        if lift.status == 'aktivna':
            lift.status = 'neaktivna'
        else:
            lift.status ='aktivna'
        lift.save()
    return redirect('ski_center_profile')


@login_required
def delete_lift(request, pk):
    """
    Briše žičaru iz ski centra.

    :model:`ski_center.Lift`

    Argumenti:  request - HTTP zahtev. (mora biti POST metoda)
                pk - Primarni ključ  žičare.

    Return: Redirect na ski_center_profile sa success porukom.
    """
    lift = get_object_or_404(Lift, pk=pk)
    if request.method == 'POST':
        lift.delete()
        messages.success(request, 'Žičara je obrisana.')
    return redirect('ski_center_profile')

def ski_center_public_profile(request, pk):
    """
    Prikazuje javni profil ski centra sa stazama, žičarama, instruktorima i recenzijama.

    :model:`ski_center.SkiCenterProfile`
    :model:`ski_center.Slope`
    :model:`ski_center.Lift`
    :model:`instructor.InstructorProfile`
    :template:`ski_center/skiCenterPublicProfile.html`

    Argumenti:  request - HTTP zahtev.
                pk - Primarni ključ ski centra.

    Return: Render skiCenterPublicProfile template sa stazama, žičarama i recenzijama.
    """
    ski_center = get_object_or_404(SkiCenterProfile, pk=pk)

    slopes = Slope.objects.filter(ski_center=ski_center)
    lifts = Lift.objects.filter(ski_center=ski_center)
    rentals = RentalProfile.objects.filter(ski_center=ski_center)

    instructors = list(InstructorProfile.objects.filter(ski_center=ski_center).select_related('business_profile__user'))
    for ins in instructors:
        ins.avg_rating = ins.reviews.filter(is_removed=False).aggregate(Avg('rating'))['rating__avg']

    slopes_count = sum(float(s.length_km) for s in slopes if s.length_km)
    lifts_count = lifts.count()
    instructors_count = len(instructors)
    rentals_count = rentals.count()
    reviews = ski_center.reviews.filter(is_removed=False).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    context = {
        'ski_center': ski_center,
        'slopes': slopes,
        'lifts': lifts,
        'instructors': instructors,
        'slopes_count': slopes_count,
        'lifts_count': lifts_count,
        'instructors_count': instructors_count,
        'rentals_count': rentals_count,
        'rentals': rentals,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'rentals': rentals,
    }

    return render(request, 'ski_center/skiCenterPublicProfile.html', context)