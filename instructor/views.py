from django.db.models import Avg, Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import BusinessProfile
from .models import InstructorProfile, TimeSlot, Booking
from .forms import InstructorProfileForm
from accounts.views import expire_pending_bookings
from django.utils import timezone
from datetime import datetime
from ski_school.models import SkiSchoolProfile
from ski_center.models import SkiCenterProfile


@login_required
def instructor_profile(request):
    """
    Prikazuje profil ulogovanog instruktora sa terminima i rezervacijama.

    :model:`instructor.InstructorProfile`
    :model:`instructor.TimeSlot`
    :model:`instructor.Booking`
    :template:`instructor/instructorProfile.html`

    Argumenti:  request - HTTP zahtev ulogovanog instruktora.

    Return:
        Render instructorProfile template sa listom termina, rezervacija i statistikama.

    """
    expire_pending_bookings()
    bp = get_object_or_404(BusinessProfile, user=request.user)
    instructor = get_object_or_404(InstructorProfile, business_profile=bp)
    reviews = instructor.reviews.filter(is_removed=False).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    time_slots = TimeSlot.objects.filter(instructor=instructor).order_by('date', 'start_time')
    bookings = Booking.objects.filter(time_slot__instructor=instructor).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    visible_bookings = bookings.filter(status=status_filter) if status_filter else bookings
    form_errors = request.session.pop('form_errors', {})

    return render(request, 'instructor/instructorProfile.html', {
        'instructor': instructor, 'time_slots': time_slots,
        'bookings': visible_bookings, 'bookings_count': bookings.count(),
        'status_filter': status_filter,
        'confirmed_count': bookings.filter(status='potvrdjena').count(),
        'completed_count': bookings.filter(status='realizovana').count(),
        'pending_count': bookings.filter(status='ceka_potvrdu').count(),
        'rejected_count': bookings.filter(status='odbijena').count(),
        'form_errors': form_errors,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'ski_schools': SkiSchoolProfile.objects.all(),
        'ski_schools': SkiSchoolProfile.objects.all(),
        'ski_centri': SkiCenterProfile.objects.select_related('business_profile').all(),
    })

@login_required
def update_instructor(request, pk):
    """
    Azurira podatke profila instruktora.

    :model:`instructor.InstructorProfile`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ instruktora.

    Return: Redirect na instructor_profile sa success porukom ili greškama u session-u.
    """
    instructor = get_object_or_404(InstructorProfile, pk=pk)
    if request.method == 'POST':
        form = InstructorProfileForm(request.POST, request.FILES)
        if form.is_valid():
            instructor.business_profile.user.first_name = form.cleaned_data['first_name']
            instructor.business_profile.user.last_name = form.cleaned_data['last_name']
            instructor.business_profile.user.save()
            instructor.specialization = form.cleaned_data['specialization']
            instructor.price_per_hour = form.cleaned_data['price_per_hour']
            instructor.years_of_experience = form.cleaned_data['years_of_experience']
            instructor.languages = form.cleaned_data['languages']
            instructor.bio = form.cleaned_data['bio']
            instructor.qualifications = form.cleaned_data['qualifications']
            if 'photo' in request.FILES:
                instructor.photo = request.FILES['photo']
            instructor.ski_school_id = request.POST.get('ski_school') or None
            instructor.ski_center_id = request.POST.get('ski_center') or None
            instructor.save()
            messages.success(request, 'Profil je uspešno ažuriran.')
            return redirect('instructor_profile')
        else:
            request.session['form_errors'] = form.errors
            return redirect('instructor_profile')
    return redirect('instructor_profile')




@login_required
def add_time_slot(request, pk):
    """
    Dodaje novi slobodan termin instruktoru.

    :model:`instructor.TimeSlot`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ instruktora.

    Return: Redirect na instructor_profile sa success porukom.
    """
    instructor = get_object_or_404(InstructorProfile, pk=pk)
    if request.method == 'POST':
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        duration = int(request.POST.get('duration', 60))
        h, m = map(int, start_time.split(':')[:2])
        end_total = h * 60 + m + duration
        TimeSlot.objects.create(
            instructor=instructor,
            date=date,
            start_time=f"{h:02d}:{m:02d}",
            end_time=f"{end_total // 60:02d}:{end_total % 60:02d}",
        )
        messages.success(request, 'Termin je dodat.')
    return redirect('instructor_profile')

@login_required
def update_time_slot(request, pk):
    """
    Menja datum i vreme postojećeg termina.
    Izmena nije moguća ako je termin već rezervisan.

    :model:`instructor.TimeSlot`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ instruktora.

    Return: Redirect na instructor_profile sa success ili error porukom.
    """
    slot = get_object_or_404(TimeSlot, pk=pk)
    if request.method == 'POST':
        if slot.is_booked:
            messages.error(request, 'Ne možete izmeniti termin koji ima aktivnu rezervaciju.')
            return redirect('instructor_profile')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        duration = int(request.POST.get('duration', 60))
        h, m = map(int, start_time.split(':')[:2])
        end_total = h * 60 + m + duration
        slot.date = date
        slot.start_time = f"{h:02d}:{m:02d}"
        slot.end_time = f"{end_total // 60:02d}:{end_total % 60:02d}"
        slot.save()
        messages.success(request, 'Termin je izmenjen.')
    return redirect('instructor_profile')

@login_required
def delete_time_slot(request, pk):
    """
    Briše slobodan termin instruktora.
    Brisanje nije moguće ako je termin rezervisan.

    :model:`instructor.TimeSlot`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ instruktora.

    Return: Redirect na instructor_profile.
    """
    slot = get_object_or_404(TimeSlot, pk=pk)
    if request.method == 'POST' and not slot.is_booked:
        slot.delete()
        messages.success(request, 'Termin je obrisan.')
    return redirect('instructor_profile')

def _get_owned_booking(request, pk):
    """
    Pomoćna funkcija koja vraća Booking objekat samo ako pripada ulogovanom instruktoru.
    Vraća None ako instruktor nema pristup ovoj rezervaciji.
    """
    booking = get_object_or_404(Booking, pk=pk)
    if booking.time_slot.instructor.business_profile.user == request.user:
        return booking
    return None

@login_required
def accept_booking(request, pk):
    """
    Potvrđuje rezervaciju klijenta.

    :model:`instructor.Booking`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ instruktora.

    Return: Redirect na instructor_profile.
    """
    booking = _get_owned_booking(request, pk)
    if booking is None:
        messages.error(request, 'Nemate pristup ovoj rezervaciji.')
    elif request.method == 'POST' and booking.status == 'ceka_potvrdu':
        booking.status = 'potvrdjena'
        booking.save()
        messages.success(request, 'Rezervacija je prihvaćena.')
    return redirect('instructor_profile')

@login_required
def reject_booking(request, pk):
    """
    Odbija rezervaciju i oslobađa termin.

    :model:`instructor.Booking`
    :model:`instructor.TimeSlot`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ rezervacije.

    Return: Redirect na instructor_profile.
    """
    booking = _get_owned_booking(request, pk)
    if booking is None:
        messages.error(request, 'Nemate pristup ovoj rezervaciji.')
    elif request.method == 'POST' and booking.status == 'ceka_potvrdu':
        booking.status = 'odbijena'
        booking.reject_reason = request.POST.get('reject_reason', '').strip()
        booking.time_slot.is_booked = False
        booking.time_slot.save()
        booking.save()
        messages.success(request, 'Rezervacija je odbijena.')
    return redirect('instructor_profile')

@login_required
def complete_booking(request, pk):
    """
    Označava rezervaciju kao realizovanu.

    :model:`instructor.Booking`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                pk - Primarni ključ rezervacije.

    Return: Redirect na instructor_profile.
    """
    booking = _get_owned_booking(request, pk)
    if booking is None:
        messages.error(request, 'Nemate pristup ovoj rezervaciji.')
    elif request.method == 'POST' and booking.status == 'potvrdjena':
        booking.status = 'realizovana'
        booking.save()
        messages.success(request, 'Čas je označen kao realizovan.')
    return redirect('instructor_profile')


def instructors_list(request):
    """
    Prikazuje listu svih instruktora sa filterima za pretragu.

    :model:`instructor.InstructorProfile`
    :template:`instructor/instructorsList.html`

    Argumenti:  request -HTTP zahtev.
    (GET parametri: q (ime), spec (specijalizacija), lokacija.)

    Return: Render instructorsList template sa filtriranom listom instruktora.
    """
    today = timezone.now().date()
    instruktori = InstructorProfile.objects.select_related(
        'business_profile__user', 'ski_center__business_profile'
    ).annotate(
        free_slots_count=Count('time_slots', filter=Q(time_slots__is_booked=False, time_slots__date__gte=today))
    ).all()
    q = request.GET.get('q', '')
    spec = request.GET.get('spec', '')
    lokacija = request.GET.get('lokacija', '')

    if q:
        instruktori = instruktori.filter(
            Q(business_profile__user__first_name__icontains=q) |
            Q(business_profile__user__last_name__icontains=q)
        )
    if spec:
        instruktori = instruktori.filter(specialization=spec)
    if lokacija:
        instruktori = instruktori.filter(business_profile__location__icontains=lokacija)

    return render(request, 'instructor/instructorsList.html', {
        'instruktori': instruktori,
        'q': q,
        'spec': spec,
        'lokacija': lokacija,
    })

def instructor_public_profile(request, pk):
    """
    Prikazuje javni profil instruktora sa slobodnim terminima.

    :model:`instructor.InstructorProfile`
    :model:`instructor.TimeSlot`
    :template:`instructor/instructorPublicProfile.html`

    Argumenti:  request - HTTP zahtev.
                pk - Primarni ključ instruktora.

    Return: Render instructorPublicProfile template sa slobodnim terminima.
    """
    instructor = get_object_or_404(InstructorProfile, pk=pk)
    reviews = instructor.reviews.filter(is_removed=False).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    now = timezone.now()
    free_slots = TimeSlot.objects.filter(
        instructor=instructor,
        is_booked=False,
        date__gte=now.date()
    ).exclude(
        date=now.date(),
        start_time__lt=now.time()
    ).order_by('date', 'start_time')
    return render(request, 'instructor/instructorPublicProfile.html', {
        'instructor': instructor,
        'free_slots': free_slots,
        'reviews': reviews,
        'avg_rating': avg_rating,
    })

@login_required
def book_slot(request, slot_pk):
    """
    Kreira rezervaciju za odabrani termin.
    Proverava dostupnost termina pre kreiranja rezervacije.

    :model:`instructor.TimeSlot`
    :model:`instructor.Booking`
    :model:`accounts.ClientProfile`

    Argumenti:  request - HTTP zahtev. Mora biti POST metoda.
                slot_pk - Primarni ključ termina koji se rezerviše.

    Return: Redirect na instructor_public_profile sa success ili error porukom.
    """
    from accounts.models import ClientProfile
    slot = get_object_or_404(TimeSlot, pk=slot_pk)
    if request.method == 'POST':
        if slot.is_booked:
            messages.error(request, 'Odabrani termin nije više dostupan. Molimo izaberite drugi termin.')
            return redirect('instructor_public_profile', pk=slot.instructor.pk)
        client = get_object_or_404(ClientProfile, user=request.user)
        Booking.objects.update_or_create(time_slot = slot, defaults = {'client': client, 'status': 'ceka_potvrdu', 'reject_reason': None},)
        slot.is_booked = True
        slot.save()
        messages.success(request, 'Rezervacija je uspešno kreirana! Čeka potvrdu instruktora.')
        return redirect('instructor_public_profile', pk=slot.instructor.pk)
    return redirect('instructor_public_profile', pk=slot.instructor.pk)