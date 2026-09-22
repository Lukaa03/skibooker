from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta

from accounts.models import ClientProfile, BusinessProfile
from rental.models import (
    RentalProfile, Equipment, EquipmentVariant, EquipmentReservation,
    Brand, EquipmentCategory,
)

class RentalPublicProfileTest(TestCase):
    """
    Testovi za SSU_04 (2.2.2) — Javni profil rental firme.
    Pregled je dostupan bez prijave.
    """

    def setUp(self):
        self.client = Client()

        self.rental_user = User.objects.create_user(
            username='rental@test.com',
            email='rental@test.com',
            password='Test1234!'
        )
        self.bp = BusinessProfile.objects.create(
            user=self.rental_user,
            business_type='rental',
            business_name='SkiRental Pro',
            location='Kopaonik'
        )
        self.rental = RentalProfile.objects.create(
            business_profile=self.bp,
            description='Opis rental firme',
            contact_phone='011123456',
        )
        self.brand = Brand.objects.create(name='Rossignol')
        self.category = EquipmentCategory.objects.create(name='Skije')
        self.equipment = Equipment.objects.create(
            rental=self.rental,
            brand=self.brand,
            model='React 6',
            category=self.category,
            price_per_day=1200,
            is_active=True,
        )

    # ===== LEGALNE KLASE =====

    def test_rental_public_profile_dostupan_bez_prijave(self):
        """Javni profil rental firme se prikazuje bez prijave (status 200)."""
        response = self.client.get(reverse('rentalPublicProfile', args=[self.rental.pk]))
        self.assertEqual(response.status_code, 200)

    def test_rental_public_profile_prikazuje_naziv(self):
        """Profil sadrži naziv rental firme."""
        response = self.client.get(reverse('rentalPublicProfile', args=[self.rental.pk]))
        self.assertContains(response, 'SkiRental Pro')

    def test_rental_public_profile_prikazuje_opremu(self):
        """Profil sadrži listu opreme u kontekstu."""
        response = self.client.get(reverse('rentalPublicProfile', args=[self.rental.pk]))
        self.assertIn('equipment_list', response.context)
        self.assertEqual(len(response.context['equipment_list']), 1)

    # ===== NELEGALNE KLASE =====

    def test_rental_public_profile_ne_postoji(self):
        """Profil rental firme koji ne postoji vraća 404."""
        response = self.client.get(reverse('rentalPublicProfile', args=[99999]))
        self.assertEqual(response.status_code, 404)


# ============================================================
# SSU_06 — Rezervacija ski opreme
# ============================================================

class EquipmentReservationTest(TestCase):
    """
    Testovi za SSU_06 — Rezervacija ski opreme od strane klijenta.

    Napomena: URL 'reserve_equipment' prima pk opreme (Equipment.pk),
    a varijanta se bira kroz polje forme (equipment_variant).
    """

    def setUp(self):
        self.client = Client()

        # Klijent
        self.client_user = User.objects.create_user(
            username='klijent@test.com',
            email='klijent@test.com',
            password='Test1234!'
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)

        # Rental firma
        self.rental_user = User.objects.create_user(
            username='rental@test.com',
            email='rental@test.com',
            password='Test1234!'
        )
        self.bp = BusinessProfile.objects.create(
            user=self.rental_user,
            business_type='rental',
            business_name='SkiRental Pro',
            location='Kopaonik'
        )
        self.rental = RentalProfile.objects.create(business_profile=self.bp)

        # Oprema
        self.brand = Brand.objects.create(name='Rossignol')
        self.category = EquipmentCategory.objects.create(name='Skije')
        self.equipment = Equipment.objects.create(
            rental=self.rental,
            brand=self.brand,
            model='React 6',
            category=self.category,
            price_per_day=1200,
            is_active=True,
        )
        self.variant = EquipmentVariant.objects.create(
            equipment=self.equipment,
            size='170cm',
            quantity=2,
        )

        self.today = date.today()
        self.start = self.today + timedelta(days=2)
        self.end = self.today + timedelta(days=5)

    # ===== LEGALNE KLASE =====

    def test_rezervacija_uspesna(self):
        """Ulogovani klijent uspešno rezerviše slobodnu opremu."""
        self.client.login(username='klijent@test.com', password='Test1234!')
        response = self.client.post(
            reverse('reserve_equipment', args=[self.equipment.pk]),
            {
                'equipment_variant': self.variant.pk,
                'quantity': 1,
                'start_date': str(self.start),
                'end_date': str(self.end),
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            EquipmentReservation.objects.filter(
                client=self.client_profile,
                equipment_variant=self.variant,
                status='ceka_potvrdu'
            ).exists()
        )

    # ===== NELEGALNE KLASE =====

    def test_rezervacija_neulogovan_korisnik(self):
        """Neulogovani korisnik se preusmerava na login."""
        response = self.client.post(
            reverse('reserve_equipment', args=[self.equipment.pk]),
            {
                'equipment_variant': self.variant.pk,
                'quantity': 1,
                'start_date': str(self.start),
                'end_date': str(self.end),
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response.url)

    def test_rezervacija_datum_vracanja_pre_preuzimanja(self):
        """Datum vraćanja pre datuma preuzimanja — sistem odbija rezervaciju."""
        self.client.login(username='klijent@test.com', password='Test1234!')
        self.client.post(
            reverse('reserve_equipment', args=[self.equipment.pk]),
            {
                'equipment_variant': self.variant.pk,
                'quantity': 1,
                'start_date': str(self.end),    # kasniiji datum kao početak
                'end_date': str(self.start),    # raniji datum kao kraj
            }
        )
        self.assertFalse(
            EquipmentReservation.objects.filter(client=self.client_profile).exists()
        )

    def test_rezervacija_datum_u_proslosti(self):
        """Datum preuzimanja u prošlosti — sistem odbija rezervaciju."""
        self.client.login(username='klijent@test.com', password='Test1234!')
        self.client.post(
            reverse('reserve_equipment', args=[self.equipment.pk]),
            {
                'equipment_variant': self.variant.pk,
                'quantity': 1,
                'start_date': str(self.today - timedelta(days=3)),
                'end_date': str(self.today + timedelta(days=1)),
            }
        )
        self.assertFalse(
            EquipmentReservation.objects.filter(client=self.client_profile).exists()
        )

    def test_rezervacija_oprema_vec_zauzeta(self):
        """Ako je sva dostupna količina rezervisana, nova rezervacija se odbija."""
        # Prva rezervacija zauzima svu količinu (quantity=2 na varijanti, rezervišemo 2)
        EquipmentReservation.objects.create(
            equipment_variant=self.variant,
            client=self.client_profile,
            start_date=self.start,
            end_date=self.end,
            quantity=2,
            status='potvrdjena'
        )
        self.client.login(username='klijent@test.com', password='Test1234!')
        self.client.post(
            reverse('reserve_equipment', args=[self.equipment.pk]),
            {
                'equipment_variant': self.variant.pk,
                'quantity': 1,
                'start_date': str(self.start),
                'end_date': str(self.end),
            }
        )
        # Treba da bude samo jedna rezervacija (ona prvobitna)
        self.assertEqual(
            EquipmentReservation.objects.filter(equipment_variant=self.variant).count(), 1
        )

    def test_rezervacija_nedostupna_oprema(self):
        """Oprema sa is_active=False nije dostupna — server vraća 404."""
        self.equipment.is_active = False
        self.equipment.save()
        self.client.login(username='klijent@test.com', password='Test1234!')
        response = self.client.post(
            reverse('reserve_equipment', args=[self.equipment.pk]),
            {
                'equipment_variant': self.variant.pk,
                'quantity': 1,
                'start_date': str(self.start),
                'end_date': str(self.end),
            }
        )
        # View radi get_object_or_404(Equipment, pk=pk, is_active=True) → 404
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            EquipmentReservation.objects.filter(client=self.client_profile).exists()
        )


# ============================================================
# SSU_10 — Upravljanje opremom rental firme
# ============================================================

class RentalEquipmentManagementTest(TestCase):
    """
    Testovi za SSU_10 — Rental firma upravlja opremom (dodaj, izmeni, status).
    """

    def setUp(self):
        self.client = Client()

        self.rental_user = User.objects.create_user(
            username='rental@test.com',
            email='rental@test.com',
            password='Test1234!'
        )
        self.bp = BusinessProfile.objects.create(
            user=self.rental_user,
            business_type='rental',
            business_name='SkiRental Pro',
            location='Kopaonik'
        )
        self.rental = RentalProfile.objects.create(business_profile=self.bp)
        self.brand = Brand.objects.create(name='Rossignol')
        self.category = EquipmentCategory.objects.create(name='Skije')
        self.equipment = Equipment.objects.create(
            rental=self.rental,
            brand=self.brand,
            model='React 6',
            category=self.category,
            price_per_day=1200,
            is_active=True,
        )

    # ===== LEGALNE KLASE =====

    def test_rental_profil_vidljiv_ulogovanom(self):
        """Ulogovana rental firma vidi svoj profil/panel."""
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.get(reverse('rental_profile'))
        self.assertEqual(response.status_code, 200)

    def test_dodavanje_opreme_uspesno(self):
        """Rental firma uspešno dodaje novu opremu."""
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.post(reverse('add_equipment'), {
            'brand': self.brand.pk,
            'model': 'Rossignol Hero',
            'category': self.category.pk,
            'price_per_day': '1500',
            'is_active': True,
            'description': 'Napredne skije',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Equipment.objects.filter(model='Rossignol Hero').exists())

    def test_izmena_opreme_uspesna(self):
        """Rental firma uspešno menja cenu opreme."""
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.post(
            reverse('update_equipment', args=[self.equipment.pk]),
            {
                'brand': self.brand.pk,
                'model': 'React 6',
                'category': self.category.pk,
                'price_per_day': '1600',
                'is_active': True,
            }
        )
        self.assertEqual(response.status_code, 302)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.price_per_day, 1600)

    def test_promena_statusa_na_nedostupno(self):
        """
        Rental firma uklanja opremu iz ponude — is_active postaje False.
        Koristi se 'delete_equipment' koji postavlja is_active=False.
        """
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.post(
            reverse('delete_equipment', args=[self.equipment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.equipment.refresh_from_db()
        self.assertFalse(self.equipment.is_active)

    def test_promena_statusa_na_dostupno(self):
        """Rental firma ponovo aktivira opremu kroz update formu."""
        self.equipment.is_active = False
        self.equipment.save()
        self.client.login(username='rental@test.com', password='Test1234!')
        self.client.post(
            reverse('update_equipment', args=[self.equipment.pk]),
            {
                'brand': self.brand.pk,
                'model': 'React 6',
                'category': self.category.pk,
                'price_per_day': '1200',
                'is_active': True,
            }
        )
        self.equipment.refresh_from_db()
        self.assertTrue(self.equipment.is_active)

    # ===== NELEGALNE KLASE =====

    def test_rental_profil_nedostupan_bez_prijave(self):
        """Neulogovani korisnik se preusmerava sa rental panela."""
        response = self.client.get(reverse('rental_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response.url)

    def test_dodavanje_opreme_bez_cene(self):
        """Dodavanje opreme bez cene nije dozvoljeno — baza ostaje nepromenjena."""
        self.client.login(username='rental@test.com', password='Test1234!')
        before_count = Equipment.objects.count()
        self.client.post(reverse('add_equipment'), {
            'brand': self.brand.pk,
            'model': 'Test Model',
            'category': self.category.pk,
            'price_per_day': '',   # prazno — nevalidno
            'is_active': True,
        })
        self.assertEqual(Equipment.objects.count(), before_count)


# ============================================================
# SSU_11 — Upravljanje rezervacijama opreme (strana rental firme)
# ============================================================

class EquipmentReservationManagementTest(TestCase):
    """
    Testovi za SSU_11 — Rental firma prihvata, odbija i evidentira rezervacije.
    """

    def setUp(self):
        self.client = Client()

        # Rental firma
        self.rental_user = User.objects.create_user(
            username='rental@test.com',
            email='rental@test.com',
            password='Test1234!'
        )
        self.bp = BusinessProfile.objects.create(
            user=self.rental_user,
            business_type='rental',
            business_name='SkiRental Pro',
            location='Kopaonik'
        )
        self.rental = RentalProfile.objects.create(business_profile=self.bp)

        # Klijent
        self.client_user = User.objects.create_user(
            username='klijent@test.com',
            email='klijent@test.com',
            password='Test1234!'
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)

        # Oprema i varijanta
        self.brand = Brand.objects.create(name='Rossignol')
        self.category = EquipmentCategory.objects.create(name='Skije')
        self.equipment = Equipment.objects.create(
            rental=self.rental,
            brand=self.brand,
            model='React 6',
            category=self.category,
            price_per_day=1200,
            is_active=True,
        )
        self.variant = EquipmentVariant.objects.create(
            equipment=self.equipment,
            size='170cm',
            quantity=1,
        )

        today = date.today()
        self.reservation = EquipmentReservation.objects.create(
            equipment_variant=self.variant,
            client=self.client_profile,
            quantity=1,
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=6),
            status='ceka_potvrdu'
        )

    # ===== LEGALNE KLASE =====

    def test_pregled_rezervacija(self):
        """Rental firma vidi listu rezervacija na svom profilu."""
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.get(reverse('rental_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('reservations', response.context)

    def test_prihvatanje_rezervacije(self):
        """Rental firma prihvata rezervaciju — status postaje 'potvrdjena'."""
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.post(
            reverse('accept_reservation', args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'potvrdjena')

    def test_odbijanje_rezervacije(self):
        """Rental firma odbija rezervaciju — status postaje 'odbijena'."""
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.post(
            reverse('reject_reservation', args=[self.reservation.pk]),
            {'reject_reason': 'Oprema nije dostupna.'}
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'odbijena')

    def test_odbijanje_sa_razlogom_cuva_razlog(self):
        """Razlog odbijanja se čuva u polju reject_reason."""
        self.client.login(username='rental@test.com', password='Test1234!')
        self.client.post(
            reverse('reject_reservation', args=[self.reservation.pk]),
            {'reject_reason': 'Servisiranje opreme.'}
        )
        self.reservation.refresh_from_db()
        self.assertIn('Servisiranje', self.reservation.reject_reason)

    def test_potvrdivanje_povratka_opreme(self):
        """Rental firma potvrđuje završetak iznajmljivanja — status postaje 'realizovana'."""
        self.reservation.status = 'potvrdjena'
        self.reservation.save()
        self.client.login(username='rental@test.com', password='Test1234!')
        response = self.client.post(
            reverse('complete_reservation', args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'realizovana')

    # ===== NELEGALNE KLASE =====

    def test_prihvatanje_vec_prihvacene_rezervacije(self):
        """Prihvatanje rezervacije koja nije 'ceka_potvrdu' ne menja status."""
        self.reservation.status = 'potvrdjena'
        self.reservation.save()
        self.client.login(username='rental@test.com', password='Test1234!')
        self.client.post(
            reverse('accept_reservation', args=[self.reservation.pk])
        )
        self.reservation.refresh_from_db()
        # View odbija jer status != 'ceka_potvrdu' — status ostaje 'potvrdjena'
        self.assertEqual(self.reservation.status, 'potvrdjena')

    def test_upravljanje_rezervacijom_bez_prijave(self):
        """Neulogovani korisnik se preusmerava sa akcija na rezervacijama."""
        response = self.client.post(
            reverse('accept_reservation', args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response.url)

    def test_upravljanje_tudim_rezervacijama(self):
        """Rental firma ne može da upravlja rezervacijama druge firme — dobija 404."""
        drugi_user = User.objects.create_user(
            username='drugi@test.com',
            email='drugi@test.com',
            password='Test1234!'
        )
        drugi_bp = BusinessProfile.objects.create(
            user=drugi_user,
            business_type='rental',
            business_name='Drugi Rental',
            location='Jahorina'
        )
        RentalProfile.objects.create(business_profile=drugi_bp)

        self.client.login(username='drugi@test.com', password='Test1234!')
        response = self.client.post(
            reverse('accept_reservation', args=[self.reservation.pk])
        )
        # View koristi get_object_or_404 sa rental filtrom — vraća 404 za tuđu rezervaciju
        self.assertEqual(response.status_code, 404)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'ceka_potvrdu')