from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.db.models import Avg
from django.contrib.admin.views.decorators import staff_member_required
from instructor.models import Booking, InstructorProfile
from datetime import datetime, timedelta
from .forms import RegistrationForm, BusinessRegistrationForm, LoginForm
from .models import ClientProfile, BusinessRequest, BusinessProfile
from ski_center.models import SkiCenterProfile
from django.core.mail import send_mail
from rental.models import EquipmentReservation
from reviews.models import Review
from .models import AdminLog


def expire_pending_bookings():
    """
    Prolazi kroz sve rezervacije sa statusom 'ceka_potvrdu' koje su starije od 24h
    i automatski ih otkazuje.

    Za svaku isteklu rezervaciju:
        - menja status na 'otkazana'
        - oslobađa termin (is_booked = False)
        - šalje email obaveštenje klijentu

    Poziva se na početku client_profile i instructor_profile viewa (lazy expiry),
    umesto background schedulera.
    """
    from instructor.models import Booking
    expired = Booking.objects.filter(
        status='ceka_potvrdu',
        created_at__lt=timezone.now() - timedelta(hours=24)
    )
    for booking in expired:
        booking.status = 'otkazana'
        booking.time_slot.is_booked = False
        booking.time_slot.save()
        booking.save()
        send_mail(
            subject='Rezervacija nije potvrđena',
            message=f'Vaša rezervacija za {booking.time_slot.date} u {booking.time_slot.start_time} nije potvrđena u predviđenom roku i automatski je otkazana.',
            from_email='noreply@skibooker.com',
            recipient_list=[booking.client.user.email],
            fail_silently=True,
        )



def register(request):
    """
    Registruje novog korisnika kao klijenta ili poslovnog korisnika.

    Klijentski nalog se aktivira odmah nakon registracije.
    Poslovni nalog se kreira sa statusom neaktivan i čeka odobrenje admina
    kroz :model:`accounts.BusinessRequest`.

    :model:`accounts.BusinessRequest`
    :model:`auth.User`
    :template:`accounts/register.html`

    Argumenti:  request - HTTP zahtev.

    Return:  Redirect na home stranicu nakon uspešne registracije, ili
             render register template sa greškama.
    """

    user_type = request.POST.get('user_type', 'client')

    if request.method == 'POST':
        if user_type == 'business':
            form = BusinessRegistrationForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    is_active=False,
                )
                BusinessRequest.objects.create(
                    user=user,
                    business_type=form.cleaned_data['business_type'],
                    business_name=form.cleaned_data['business_name'],
                    location=form.cleaned_data['location'],
                    status='na_cekanju',
                )
                messages.info(request, 'Vaš zahtev je primljen. Nalog će biti aktiviran nakon odobrenja administratora.')
                return redirect('home')
        else:

            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                )
                ClientProfile.objects.create(user=user)
                login(request, user)
                messages.success(request, 'Uspešno ste se registrovali! Dobrodošli na SkiBooker.')
                return redirect('home')

    return render(request, 'accounts/register.html', {
        'client_form': RegistrationForm(request.POST if user_type == 'client' and request.method == 'POST' else None),
        'business_form': BusinessRegistrationForm(request.POST if user_type == 'business' and request.method == 'POST' else None),
        'ski_centri': SkiCenterProfile.objects.select_related('business_profile').all(),
    })


def login_view(request):
    """
    Prijavljuje korisnika u sistem.

    :template:`accounts/login.html`

    Argumenti:  request - HTTP zahtev.

    Return: Redirect na home stranicu nakon uspešne prijave, ili
            render login template sa greškom ako su uneti podaci neispravni
            ili nalog nije aktivan.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    try:
                        from accounts.models import BusinessProfile
                        from ski_center.models import SkiCenterProfile
                        bp = BusinessProfile.objects.get(user=user)
                        if bp.business_type != 'ski_center':
                            sc = SkiCenterProfile.objects.filter(
                                business_profile__location__icontains=bp.location).first()
                            if sc:
                                if bp.business_type == 'instructor':
                                    from instructor.models import InstructorProfile
                                    ins = InstructorProfile.objects.get(business_profile=bp)
                                    if not ins.ski_center:
                                        ins.ski_center = sc
                                        ins.save()
                                elif bp.business_type == 'rental':
                                    from rental.models import RentalProfile
                                    rp = RentalProfile.objects.get(business_profile=bp)
                                    if not rp.ski_center:
                                        rp.ski_center = sc
                                        rp.save()
                                elif bp.business_type == 'ski_skola':
                                    from ski_school.models import SkiSchoolProfile
                                    ss = SkiSchoolProfile.objects.get(business_profile=bp)
                                    if not ss.ski_center:
                                        ss.ski_center = sc
                                        ss.save()
                    except Exception:
                        pass

                    return redirect('home')
                else:
                    messages.error(request, 'Vaš nalog nije validan za prijavu.')
            else:
                messages.error(request, 'Pogrešan email ili lozinka.')
    form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def home(request):
    """
    Prikazuje početnu stranicu aplikacije i
    određuje tip korisnika za personalizovan prikaz sadržaja.

    :template:`accounts/home.html`

    Argumenti:  request - HTTP zahtev trenutnog korisnika.

    Return: Render home template sa kontekstom: user_role, instruktori (top 4),
            ski_centri (top 3) i reviews (poslednjih 6 recenzija).
    """
    instruktori = InstructorProfile.objects.select_related('business_profile__user').all()[:4]
    ski_centri = SkiCenterProfile.objects.select_related(
        'business_profile'
    ).prefetch_related('slopes', 'lifts')[:3]
    reviews = Review.objects.filter(is_removed=False).select_related(
        'reviewer__user'
    ).order_by('-created_at')[:6]
    user_role = None
    if request.user.is_authenticated:
        if hasattr(request.user, 'clientprofile'):
            user_role = 'klijent'
        elif hasattr(request.user, 'businessprofile'):
            user_role = request.user.businessprofile.business_type
    return render(request, 'accounts/home.html', {
        'user_role': user_role,
        'instruktori': instruktori,
        'ski_centri': ski_centri,
        'reviews': reviews,
    })



@login_required
def client_profile(request):
    """
    Prikazuje profil klijentskog korisnika sa pregledom rezervacija.
    Aktivne rezervacije dobijaju can_cancel flag (otkazivanje moguće ako je
    ostalo više od 24h do termina). Prethodne rezervacije dobijaju has_review
    flag koji označava da li je klijent već ostavio recenziju.

    :model:`accounts.ClientProfile`
    :model:`instructor.Booking`
    :template:`accounts/clientProfile.html`

    Argumenti:  request - HTTP zahtev ulogovanog korisnika.

    Return: Render clientProfile template sa aktivnim i prethodnim rezervacijama.
    """
    expire_pending_bookings()
    client = get_object_or_404(ClientProfile, user=request.user)
    now = timezone.now()
    all_bookings = Booking.objects.filter(client=client).select_related(
        'time_slot', 'time_slot__instructor', 'time_slot__instructor__business_profile__user'
    ).order_by('-time_slot__date', '-time_slot__start_time')

    active_bookings = all_bookings.filter(status__in=['ceka_potvrdu', 'potvrdjena'])
    past_bookings = list(all_bookings.filter(status__in=['realizovana', 'otkazana']))
    reviewed_booking_ids = set(Review.objects.filter(booking__in=past_bookings).values_list('booking_id', flat=True))
    for b in past_bookings:
        b.has_review = b.id in reviewed_booking_ids

    rental_reservations = list(EquipmentReservation.objects.filter(
        client=client, status='realizovana'
    ).select_related('equipment_variant__equipment__rental__business_profile'))
    reviewed_ids = set(Review.objects.filter(reservation__in=rental_reservations).values_list('reservation_id', flat=True))
    for res in rental_reservations:
        res.has_review = res.id in reviewed_ids

    active_bookings_list = []
    for booking in active_bookings:
        slot_dt = datetime.combine(booking.time_slot.date, booking.time_slot.start_time)
        slot_dt = timezone.make_aware(slot_dt)
        booking.can_cancel = (slot_dt - timezone.now()) >= timedelta(hours=24)
        active_bookings_list.append(booking)

    eq_qs = EquipmentReservation.objects.select_related(
        'equipment_variant__equipment__brand',
        'equipment_variant__equipment__rental__business_profile'
    ).filter(client=client)

    active_equipment = eq_qs.filter(
        status__in=['ceka_potvrdu', 'potvrdjena']
    ).order_by('-start_date')

    return render(request, 'accounts/clientProfile.html', {
        'client': client,
        'active_bookings': active_bookings_list,
        'past_bookings': past_bookings,
        'now': now,
        'active_equipment': active_equipment,
        'active_equipment_count': active_equipment.count(),
        'rental_reservations': rental_reservations,
        'past_total': len(past_bookings) + len(rental_reservations),
    })

@login_required
def cancel_booking(request, pk):
    """
    Otkazuje rezervaciju klijenta.
    Otkazivanje nije moguće ako je do termina ostalo manje od 24h.

    :model:`accounts.ClientProfile`
    :model:`instructor.Booking`

    Argumenti: request - HTTP zahtev. Mora biti POST metoda.
               pk - Primarni ključ rezervacije.

    Return: Redirect na client_profile sa success ili error porukom.
    """

    client = get_object_or_404(ClientProfile, user=request.user)
    booking = get_object_or_404(Booking, pk=pk, client=client)

    if request.method == 'POST':
        slot_datetime = datetime.combine(booking.time_slot.date, booking.time_slot.start_time)
        slot_datetime = timezone.make_aware(slot_datetime)

        if slot_datetime - timezone.now() < timedelta(hours=24):
            messages.error(request, 'Otkazivanje ove rezervacije više nije moguće u skladu sa pravilima sistema.')
            return redirect('client_profile')

        booking.status = 'otkazana'
        booking.time_slot.is_booked = False
        booking.time_slot.save()
        booking.save()
        messages.success(request, 'Rezervacija je uspešno otkazana.')
        send_mail(
            subject='Rezervacija otkazana',
            message=f'Klijent {request.user.get_full_name()} je otkazao rezervaciju za {booking.time_slot.date} u {booking.time_slot.start_time}.',
            from_email='noreply@skibooker.com',
            recipient_list=[booking.time_slot.instructor.business_profile.user.email],
            fail_silently=True,
        )

    return redirect('client_profile')

@login_required
def cancel_equipment_reservation(request, pk):
    """
    Otkazuje rezervaciju opreme klijenta.

    :model:`accounts.ClientProfile`
    :model:`rental.EquipmentReservation`

    Argumenti: request - HTTP zahtev ( Mora biti POST metoda )
               pk - Primarni ključ rezervacije opreme.

    Return: Redirect na client_profile sa success porukom.
    """
    from rental.models import EquipmentReservation
    client = get_object_or_404(ClientProfile, user=request.user)
    rez = get_object_or_404(EquipmentReservation, pk=pk, client=client)
    if request.method == 'POST':
        rez.status = 'otkazana'
        rez.save()
        messages.success(request, 'Rezervacija opreme je uspešno otkazana.')
        send_mail(
            subject='Rezervacija opreme otkazana',
            message=f'Klijent {request.user.get_full_name()} je otkazao rezervaciju opreme {rez.equipment_variant.equipment.brand.name} {rez.equipment_variant.equipment.model} za period {rez.start_date} – {rez.end_date}.',
            from_email='noreply@skibooker.com',
            recipient_list=[rez.equipment_variant.equipment.rental.business_profile.user.email],
            fail_silently=True,
        )
    return redirect('client_profile')

@staff_member_required
def admin_statistics(request):
    clients_count = ClientProfile.objects.count()
    business_by_type = {}
    for value, label in BusinessProfile.BUSINESS_TYPE_CHOICES:
        business_by_type[label] = BusinessProfile.objects.filter(business_type=value).count()

    return render(request, 'accounts/adminStatistika.html', {
        'total_users': User.objects.count(),
        'clients_count': clients_count,
        'business_by_type': business_by_type,
        'pending_requests': BusinessRequest.objects.filter(status='na_cekanju').count(),
        'active_bookings': Booking.objects.filter(status__in=['ceka_potvrdu', 'potvrdjena']).count(),
        'completed_bookings': Booking.objects.filter(status='realizovana').count(),
        'completed_rentals': EquipmentReservation.objects.filter(status='realizovana').count(),
        'avg_instructor': Review.objects.filter(instructor__isnull=False, is_removed=False).aggregate(Avg('rating'))['rating__avg'],
        'avg_ski_center': Review.objects.filter(ski_center__isnull=False, is_removed=False).aggregate(Avg('rating'))['rating__avg'],
        'avg_rental': Review.objects.filter(rental__isnull=False, is_removed=False).aggregate(Avg('rating'))['rating__avg'],
        'requests_pending': BusinessRequest.objects.filter(status='na_cekanju').order_by('-created_at'),
    })

@staff_member_required
def approve_request(request, pk):
    req = get_object_or_404(BusinessRequest, pk=pk)
    if request.method == 'POST' and req.status == 'na_cekanju':
        user = req.user
        user.is_active = True
        user.save()
        bp, _ = BusinessProfile.objects.get_or_create(
            user=user,
            defaults={'business_type': req.business_type, 'business_name': req.business_name, 'location': req.location}
        )
        if req.business_type == 'instructor':
            from instructor.models import InstructorProfile
            InstructorProfile.objects.get_or_create(business_profile=bp)
        elif req.business_type == 'ski_center':
            from ski_center.models import SkiCenterProfile
            SkiCenterProfile.objects.get_or_create(business_profile=bp)
        elif req.business_type == 'rental':
            from rental.models import RentalProfile
            RentalProfile.objects.get_or_create(business_profile=bp)
        elif req.business_type == 'ski_skola':
            from ski_school.models import SkiSchoolProfile
            SkiSchoolProfile.objects.get_or_create(business_profile=bp)
        req.status = 'odobreno'
        req.save()
        log_admin_action(request, 'odobri_zahtev', target=req.business_name)
        send_mail(
            subject='Vas nalog je odobren',
            message=f'Poštovani, vaš zahtev za nalog "{req.business_name}" je odobren. Sada se možete prijaviti na SkiBooker.',
            from_email='noreply@skibooker.com',
            recipient_list=[user.email],
            fail_silently=True,
        )
        messages.success(request, f'Nalog "{req.business_name}" je odobren.')
    return redirect('admin_statistics')

@staff_member_required
def reject_request(request, pk):
    req = get_object_or_404(BusinessRequest, pk=pk)
    if request.method == 'POST' and req.status == 'na_cekanju':
        req.status = 'odbijeno'
        req.reject_reason = request.POST.get('reject_reason', '').strip()
        req.save()
        send_mail(
            subject='Vaš zahtev je odbijen',
            message=f'Poštovani, vaš zahtev za nalog "{req.business_name}" je odbijen. Razlog: {req.reject_reason or "nije naveden"}.',
            from_email='noreply@skibooker.com',
            recipient_list=[req.user.email],
            fail_silently=True,
        )
        log_admin_action(request, 'odbij_zahtev', target=req.business_name, details=req.reject_reason)
        messages.info(request, f'Zahtev "{req.business_name}" je odbijen.')
    return redirect('admin_statistics')

def log_admin_action(request, action, target='', details=''):
    AdminLog.objects.create(
        admin=request.user if request.user.is_authenticated else None,
        action=action, target=target, details=details or '',
    )