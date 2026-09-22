"""
Cross-testovi (Luka Stojanovic).

Django unit testovi za:
    SSU_01 – Registracija
    SSU_02 – Prijava
    SSU_07 – Pregled i otkazivanje rezervacija

Pokretanje:  python manage.py test accounts
selenijum testova: python crosstestovi/ssu01_registracija_webdriver.py
"""
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import ClientProfile, BusinessRequest, BusinessProfile


class SSU01RegistracijaTest(TestCase):
    """SSU_01 – Registracija klijenta i poslovnog korisnika."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')

    # ---------- LEGALNE KLASE (uspešan tok) ----------

    def test_get_register_stranica(self):
        """Otvaranje registracione stranice (GET) vraća 200 i pravi template."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/register.html')

    def test_uspesna_registracija_klijenta(self):
        """Validan klijent: nalog je aktivan, napravljen ClientProfile, redirect na home, ulogovan."""
        data = {
            'user_type': 'client',
            'first_name': 'Pera', 'last_name': 'Peric',
            'email': 'pera@test.rs',
            'password': 'lozinka123', 'confirm_password': 'lozinka123',
        }
        resp = self.client.post(self.url, data)
        self.assertRedirects(resp, reverse('home'))
        u = User.objects.get(email='pera@test.rs')
        self.assertTrue(u.is_active)
        self.assertTrue(ClientProfile.objects.filter(user=u).exists())
        self.assertIn('_auth_user_id', self.client.session)  # odmah ulogovan

    def test_uspesna_registracija_poslovnog(self):
        """Validan poslovni nalog: neaktivan, napravljen BusinessRequest 'na_cekanju', bez ClientProfile."""
        data = {
            'user_type': 'business',
            'email': 'firma@test.rs',
            'password': 'lozinka123', 'confirm_password': 'lozinka123',
            'business_type': 'ski_center',
            'business_name': 'Ski Centar Test',
            'location': 'Kopaonik',
        }
        resp = self.client.post(self.url, data)
        self.assertRedirects(resp, reverse('home'))
        u = User.objects.get(email='firma@test.rs')
        self.assertFalse(u.is_active)  # čeka odobrenje admina
        self.assertTrue(BusinessRequest.objects.filter(user=u, status='na_cekanju').exists())
        self.assertFalse(ClientProfile.objects.filter(user=u).exists())

    # ---------- NELEGALNE KLASE (greške / loši podaci) ----------

    def test_lozinke_se_ne_poklapaju(self):
        """password != confirm_password -> nalog se ne kreira, ostaje na formi."""
        data = {
            'user_type': 'client',
            'first_name': 'Pera', 'last_name': 'Peric',
            'email': 'nepoklapanje@test.rs',
            'password': 'lozinka123', 'confirm_password': 'druga123',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(email='nepoklapanje@test.rs').exists())

    def test_zauzet_email(self):
        """Email već postoji -> ne kreira se drugi nalog."""
        User.objects.create_user(username='zauzet@test.rs', email='zauzet@test.rs', password='lozinka123')
        data = {
            'user_type': 'client',
            'first_name': 'Pera', 'last_name': 'Peric',
            'email': 'zauzet@test.rs',
            'password': 'lozinka123', 'confirm_password': 'lozinka123',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(email='zauzet@test.rs').count(), 1)

    def test_kratka_lozinka(self):
        """Lozinka kraća od 8 karaktera -> nalog se ne kreira."""
        data = {
            'user_type': 'client',
            'first_name': 'Pera', 'last_name': 'Peric',
            'email': 'kratka@test.rs',
            'password': '123', 'confirm_password': '123',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(email='kratka@test.rs').exists())

    def test_poslovni_bez_obaveznih_polja(self):
        """Poslovni bez lokacije/naziva -> BusinessRequest se ne kreira."""
        data = {
            'user_type': 'business',
            'email': 'nepotpun@test.rs',
            'password': 'lozinka123', 'confirm_password': 'lozinka123',
            'business_type': 'ski_center',
            'business_name': '',
            'location': '',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(BusinessRequest.objects.filter(user__email='nepotpun@test.rs').exists())


class SSU02PrijavaTest(TestCase):
    """SSU_02 – Prijava (login). Prijava ide preko email adrese."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('login')
        # aktivan nalog za uspešnu prijavu (username = email, jer login ide preko email-a)
        self.user = User.objects.create_user(
            username='klijent@test.rs', email='klijent@test.rs',
            password='lozinka123', is_active=True,
        )

    # ---------- LEGALNE KLASE ----------

    def test_get_login_stranica(self):
        """GET otvara stranicu za prijavu."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/login.html')

    def test_uspesna_prijava(self):
        """Tačan email + lozinka aktivnog naloga -> ulogovan, redirect na home."""
        resp = self.client.post(self.url, {'email': 'klijent@test.rs', 'password': 'lozinka123'})
        self.assertRedirects(resp, reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    # ---------- NELEGALNE KLASE ----------

    def test_pogresna_lozinka(self):
        """Pogrešna lozinka -> nije ulogovan, ostaje na login stranici."""
        resp = self.client.post(self.url, {'email': 'klijent@test.rs', 'password': 'pogresna'})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_nepostojeci_email(self):
        """Nepostojeći email -> nije ulogovan."""
        resp = self.client.post(self.url, {'email': 'nema@test.rs', 'password': 'lozinka123'})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_neaktivan_nalog(self):
        """Poslovni nalog koji čeka odobrenje (is_active=False) ne može da se prijavi."""
        User.objects.create_user(
            username='neaktivan@test.rs', email='neaktivan@test.rs',
            password='lozinka123', is_active=False,
        )
        resp = self.client.post(self.url, {'email': 'neaktivan@test.rs', 'password': 'lozinka123'})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_prazna_polja(self):
        """Prazan email i lozinka -> nije ulogovan."""
        resp = self.client.post(self.url, {'email': '', 'password': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class SSU07PregledRezervacijaTest(TestCase):
    """
    SSU_07 – Pregled i otkazivanje rezervacija.

    Testira `client_profile` (pregled) i `cancel_booking` (otkazivanje).
    Pravilo (2.3): otkazivanje nije moguce u roku kracem od 24h pre termina.
    """

    def setUp(self):
        self.client = Client()

        # --- Klijent ---
        self.klijent_user = User.objects.create_user(
            username='klijent7@test.rs', email='klijent7@test.rs',
            password='lozinka123', first_name='Ana', last_name='Anic', is_active=True,
        )
        self.client_profile = ClientProfile.objects.create(user=self.klijent_user)

        # --- Instruktor (za termine) ---
        self.instr_user = User.objects.create_user(
            username='instruktor7@test.rs', email='instruktor7@test.rs',
            password='lozinka123', first_name='Zika', last_name='Zikic', is_active=True,
        )
        self.instr_bp = BusinessProfile.objects.create(
            user=self.instr_user, business_type='instructor',
            business_name='Zika Zikic', location='Kopaonik',
        )
        from instructor.models import InstructorProfile
        self.instructor = InstructorProfile.objects.create(
            business_profile=self.instr_bp, price_per_hour=3000, years_of_experience=5,
        )
        self.url = reverse('client_profile')

    def _napravi_booking(self, sati_do_termina=72, status='potvrdjena', client_profile=None):
        """Pomocna: kreira termin za `sati_do_termina` u buducnosti + rezervaciju."""
        from instructor.models import TimeSlot, Booking
        slot_dt = timezone.now() + timedelta(hours=sati_do_termina)
        end_dt = slot_dt + timedelta(hours=1)
        slot = TimeSlot.objects.create(
            instructor=self.instructor, date=slot_dt.date(),
            start_time=slot_dt.time().replace(microsecond=0),
            end_time=end_dt.time().replace(microsecond=0),
            is_booked=True,
        )
        return Booking.objects.create(
            client=client_profile or self.client_profile, time_slot=slot, status=status,
        )

    # ---------- LEGALNE KLASE (uspešan tok) ----------

    def test_pregled_liste_rezervacija(self):
        """
        2.2.1 – Prijavljen klijent otvara profil i vidi svoje rezervacije
        (aktivnu i prethodnu) sa statusom 200.
        """
        aktivna = self._napravi_booking(sati_do_termina=72, status='potvrdjena')
        self._napravi_booking(sati_do_termina=-48, status='realizovana')  # prethodna
        self.client.force_login(self.klijent_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/clientProfile.html')
        self.assertIn(aktivna, resp.context['active_bookings'])
        self.assertEqual(len(resp.context['past_bookings']), 1)

    def test_uspesno_otkazivanje(self):
        """
        2.2.2 – Otkazivanje aktivne rezervacije (termin > 24h):
        status -> 'otkazana', termin oslobodjen (is_booked=False).
        """
        booking = self._napravi_booking(sati_do_termina=72, status='potvrdjena')
        self.client.force_login(self.klijent_user)
        resp = self.client.post(reverse('cancel_booking', args=[booking.pk]))
        self.assertRedirects(resp, self.url)
        booking.refresh_from_db()
        booking.time_slot.refresh_from_db()
        self.assertEqual(booking.status, 'otkazana')
        self.assertFalse(booking.time_slot.is_booked)

    def test_prazan_profil_bez_rezervacija(self):
        """2.2.4 – Klijent bez rezervacija: profil se otvara (200), liste su prazne."""
        self.client.force_login(self.klijent_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['active_bookings']), 0)
        self.assertEqual(len(resp.context['past_bookings']), 0)

    # ---------- NELEGALNE KLASE (greške / nedozvoljen pristup) ----------

    def test_otkazivanje_van_perioda(self):
        """
        2.2.3 – Otkazivanje u roku kracem od 24h nije dozvoljeno:
        status ostaje nepromenjen, termin i dalje zauzet.
        """
        booking = self._napravi_booking(sati_do_termina=2, status='potvrdjena')
        self.client.force_login(self.klijent_user)
        resp = self.client.post(reverse('cancel_booking', args=[booking.pk]))
        self.assertRedirects(resp, self.url)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'potvrdjena')  # nije otkazana
        self.assertTrue(booking.time_slot.is_booked)

    def test_neulogovan_pristup_profilu(self):
        """Neprijavljen korisnik -> login_required preusmerava na prijavu."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp.url)

    def test_otkazivanje_tudje_rezervacije(self):
        """
        Klijent ne moze da otkaze tudju rezervaciju:
        cancel_booking filtrira po client -> get_object_or_404 vraca 404.
        """
        drugi_user = User.objects.create_user(
            username='drugi7@test.rs', email='drugi7@test.rs',
            password='lozinka123', is_active=True,
        )
        drugi_cp = ClientProfile.objects.create(user=drugi_user)
        tudja = self._napravi_booking(sati_do_termina=72, status='potvrdjena', client_profile=drugi_cp)
        self.client.force_login(self.klijent_user)
        resp = self.client.post(reverse('cancel_booking', args=[tudja.pk]))
        self.assertEqual(resp.status_code, 404)
        tudja.refresh_from_db()
        self.assertEqual(tudja.status, 'potvrdjena')

    def test_get_metoda_ne_otkazuje(self):
        """GET umesto POST na cancel_booking -> rezervacija ostaje aktivna."""
        booking = self._napravi_booking(sati_do_termina=72, status='potvrdjena')
        self.client.force_login(self.klijent_user)
        resp = self.client.get(reverse('cancel_booking', args=[booking.pk]))
        self.assertRedirects(resp, self.url)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'potvrdjena')

    def test_poslovni_korisnik_bez_client_profila(self):
        """Poslovni korisnik nema ClientProfile -> profil vraca 404."""
        self.client.force_login(self.instr_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)
