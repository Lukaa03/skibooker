"""
Cross-testovi (Luka Stojanovic).

Django unit testovi za:
    SSU_05 – Rezervacija casa

Pokretanje:  python manage.py test instructor
Selenium testovi: python crosstestovi/ssu05_rezervacija_webdriver.py
"""
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import ClientProfile, BusinessProfile
from instructor.models import InstructorProfile, TimeSlot, Booking


class SSU05RezervacijaCasaTest(TestCase):
    """
    SSU_05 – Rezervacija casa.

    Testira view `book_slot` (POST /slot/<slot_pk>/book/):
    prijavljeni klijent rezervise slobodan termin instruktora.

    Napomena o dokumentaciji: specifikacija (2.3) pominje pravilo
    'najmanje 24h pre termina', ali AKTUELNA implementacija `book_slot`
    to ne proverava — jedina provera je `slot.is_booked`. Testovi prate
    stvarno ponasanje koda (cross-testiranje), ne spec.
    """

    def setUp(self):
        self.client = Client()

        # --- Klijent koji rezervise (ima ClientProfile) ---
        self.klijent_user = User.objects.create_user(
            username='klijent5@test.rs', email='klijent5@test.rs',
            password='lozinka123', first_name='Mika', last_name='Mikic',
            is_active=True,
        )
        self.client_profile = ClientProfile.objects.create(user=self.klijent_user)

        # --- Instruktor (User + BusinessProfile + InstructorProfile) ---
        self.instr_user = User.objects.create_user(
            username='instruktor5@test.rs', email='instruktor5@test.rs',
            password='lozinka123', first_name='Zika', last_name='Zikic',
            is_active=True,
        )
        self.instr_bp = BusinessProfile.objects.create(
            user=self.instr_user, business_type='instructor',
            business_name='Zika Zikic', location='Kopaonik',
        )
        self.instructor = InstructorProfile.objects.create(
            business_profile=self.instr_bp, price_per_hour=3000, years_of_experience=5,
        )

        # --- Slobodan termin za 3 dana (u buducnosti) ---
        buduci_datum = timezone.now().date() + timedelta(days=3)
        self.slot = TimeSlot.objects.create(
            instructor=self.instructor, date=buduci_datum,
            start_time='10:00', end_time='11:00', is_booked=False,
        )
        self.url = reverse('book_slot', args=[self.slot.pk])

    # ---------- LEGALNE KLASE (uspešan tok) ----------

    def test_uspesna_rezervacija(self):
        """
        2.2.1 – Prijavljen klijent rezervise slobodan termin:
        kreira se Booking (status 'ceka_potvrdu'), redirect na javni profil instruktora.
        """
        self.client.force_login(self.klijent_user)
        resp = self.client.post(self.url)
        self.assertRedirects(
            resp, reverse('instructor_public_profile', args=[self.instructor.pk])
        )
        booking = Booking.objects.get(time_slot=self.slot)
        self.assertEqual(booking.client, self.client_profile)
        self.assertEqual(booking.status, 'ceka_potvrdu')

    def test_termin_postaje_zauzet(self):
        """2.5 – Nakon rezervacije termin je oznacen kao zauzet (is_booked=True)."""
        self.client.force_login(self.klijent_user)
        self.client.post(self.url)
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)

    # ---------- NELEGALNE KLASE (greške / nedozvoljen pristup) ----------

    def test_neulogovan_korisnik(self):
        """
        2.2.4 – Neprijavljen korisnik ne moze da rezervise:
        login_required preusmerava na stranicu za prijavu, Booking se ne kreira.
        """
        resp = self.client.post(self.url)  # bez force_login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp.url)
        self.assertFalse(Booking.objects.filter(time_slot=self.slot).exists())

    def test_termin_vec_zauzet(self):
        """
        2.2.2 – Termin je u medjuvremenu zauzet (is_booked=True):
        rezervacija se ne kreira, termin ostaje netaknut.
        """
        self.slot.is_booked = True
        self.slot.save()
        self.client.force_login(self.klijent_user)
        resp = self.client.post(self.url)
        self.assertRedirects(
            resp, reverse('instructor_public_profile', args=[self.instructor.pk])
        )
        self.assertFalse(Booking.objects.filter(time_slot=self.slot).exists())

    def test_get_metoda_ne_kreira_rezervaciju(self):
        """GET umesto POST -> nema rezervacije, termin ostaje slobodan."""
        self.client.force_login(self.klijent_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Booking.objects.filter(time_slot=self.slot).exists())
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_booked)

    def test_poslovni_korisnik_bez_client_profila(self):
        """
        Poslovni korisnik (instruktor) nema ClientProfile ->
        get_object_or_404(ClientProfile) vraca 404, rezervacija se ne kreira.
        """
        self.client.force_login(self.instr_user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(Booking.objects.filter(time_slot=self.slot).exists())

    def test_nepostojeci_termin(self):
        """Rezervacija termina koji ne postoji (nevalidan pk) -> 404."""
        self.client.force_login(self.klijent_user)
        resp = self.client.post(reverse('book_slot', args=[999999]))
        self.assertEqual(resp.status_code, 404)
