"""
Cross-testovi (Luka Stojanovic).

Django unit testovi za:
    SSU_09 – Upravljanje profilom ski centra
    SSU_03 – Pregled ski centara (lista, pretraga, sortiranje, javni detalj)

Pokretanje:  python manage.py test ski_center
Selenium testovi: python crosstestovi/ssu09_ski_centar_webdriver.py
                  python crosstestovi/ssu03_ski_centri_webdriver.py
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import ClientProfile, BusinessProfile
from ski_center.models import SkiCenterProfile, Slope, Lift
from reviews.models import Review


class SSU09UpravljanjeSkiCentromTest(TestCase):
    """
    SSU_09 – Upravljanje profilom ski centra.

    Testira views: ski_center_profile (pregled), update_ski_center (azuriranje),
    add_slope / change_slope_status / delete_slope (staze),
    add_lift / change_lift_status / delete_lift (zicare).
    """

    def setUp(self):
        self.client = Client()
        self.sc_user = User.objects.create_user(
            username='centar@test.rs', email='centar@test.rs',
            password='lozinka123', is_active=True,
        )
        self.sc_bp = BusinessProfile.objects.create(
            user=self.sc_user, business_type='ski_center',
            business_name='Ski Centar Kop', location='Kopaonik',
        )
        self.ski_center = SkiCenterProfile.objects.create(
            business_profile=self.sc_bp, description='Najveci centar',
            contact_email='info@kop.rs', contact_phone='011111',
        )
        self.slope = Slope.objects.create(
            ski_center=self.ski_center, name='Karaman', length_km=3, difficulty='crvena', status='otvorena',
        )
        self.lift = Lift.objects.create(
            ski_center=self.ski_center, name='Gvozdac', status='aktivna',
        )

    def test_get_profil_ski_centra(self):
        self.client.force_login(self.sc_user)
        resp = self.client.get(reverse('ski_center_profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'ski_center/skiCenterProfile.html')
        self.assertEqual(resp.context['ski_center'], self.ski_center)

    def test_azuriranje_profila(self):
        self.client.force_login(self.sc_user)
        data = {
            'business_name': 'Ski Centar Kopaonik', 'location': 'Kopaonik',
            'contact_email': 'novi@kop.rs', 'contact_phone': '022222',
            'website': 'https://kop.rs', 'description': 'Azuriran opis',
            'latitude': '43.28', 'longitude': '20.80',
        }
        resp = self.client.post(reverse('update_ski_center', args=[self.ski_center.pk]), data)
        self.assertRedirects(resp, reverse('ski_center_profile'))
        self.ski_center.refresh_from_db()
        self.sc_bp.refresh_from_db()
        self.assertEqual(self.ski_center.contact_email, 'novi@kop.rs')
        self.assertEqual(self.ski_center.description, 'Azuriran opis')
        self.assertEqual(self.sc_bp.business_name, 'Ski Centar Kopaonik')

    def test_dodavanje_staze(self):
        self.client.force_login(self.sc_user)
        data = {'name': 'Malo jezero', 'length_km': '1.5', 'difficulty': 'plava', 'status': 'otvorena'}
        resp = self.client.post(reverse('add_slope', args=[self.ski_center.pk]), data)
        self.assertRedirects(resp, reverse('ski_center_profile'))
        self.assertTrue(Slope.objects.filter(ski_center=self.ski_center, name='Malo jezero').exists())

    def test_dodavanje_zicare(self):
        self.client.force_login(self.sc_user)
        resp = self.client.post(reverse('add_lift', args=[self.ski_center.pk]), {'name': 'Pancicev vrh'})
        self.assertRedirects(resp, reverse('ski_center_profile'))
        lift = Lift.objects.get(ski_center=self.ski_center, name='Pancicev vrh')
        self.assertEqual(lift.status, 'aktivna')

    def test_promena_statusa_staze(self):
        self.client.force_login(self.sc_user)
        resp = self.client.post(reverse('change_slope_status', args=[self.slope.pk]))
        self.assertRedirects(resp, reverse('ski_center_profile'))
        self.slope.refresh_from_db()
        self.assertEqual(self.slope.status, 'zatvorena')

    def test_brisanje_zicare(self):
        self.client.force_login(self.sc_user)
        resp = self.client.post(reverse('delete_lift', args=[self.lift.pk]))
        self.assertRedirects(resp, reverse('ski_center_profile'))
        self.assertFalse(Lift.objects.filter(pk=self.lift.pk).exists())

    def test_neulogovan_pristup_profilu(self):
        resp = self.client.get(reverse('ski_center_profile'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp.url)

    def test_get_metoda_ne_dodaje_stazu(self):
        self.client.force_login(self.sc_user)
        pre = Slope.objects.filter(ski_center=self.ski_center).count()
        resp = self.client.get(reverse('add_slope', args=[self.ski_center.pk]))
        self.assertRedirects(resp, reverse('ski_center_profile'))
        self.assertEqual(Slope.objects.filter(ski_center=self.ski_center).count(), pre)

    def test_brisanje_nepostojece_staze(self):
        self.client.force_login(self.sc_user)
        resp = self.client.post(reverse('delete_slope', args=[999999]))
        self.assertEqual(resp.status_code, 404)

    def test_korisnik_bez_ski_center_profila(self):
        klijent_user = User.objects.create_user(
            username='klijent9@test.rs', email='klijent9@test.rs',
            password='lozinka123', is_active=True,
        )
        ClientProfile.objects.create(user=klijent_user)
        self.client.force_login(klijent_user)
        resp = self.client.get(reverse('ski_center_profile'))
        self.assertEqual(resp.status_code, 404)


def _napravi_centar(naziv, lokacija, opis=""):
    user = User.objects.create_user(
        username=f"{naziv}@sc.rs", email=f"{naziv}@sc.rs",
        password="lozinka123", is_active=True,
    )
    bp = BusinessProfile.objects.create(
        user=user, business_type="ski_center",
        business_name=naziv, location=lokacija,
    )
    return SkiCenterProfile.objects.create(business_profile=bp, description=opis)


def _dodaj_ocenu(ski_center, ocena):
    n = Review.objects.count()
    u = User.objects.create_user(username=f"rev{n}@rev.rs", email=f"rev{n}@rev.rs",
                                 password="lozinka123")
    cp = ClientProfile.objects.create(user=u)
    Review.objects.create(reviewer=cp, ski_center=ski_center, rating=ocena)


class SSU03PregledSkiCentaraTest(TestCase):
    """SSU_03 – Pregled ski centara (lista + pretraga + sort + javni detalj)."""

    def setUp(self):
        self.client = Client()
        self.lista_url = reverse('ski_centri_lista')
        self.kop = _napravi_centar("Kopaonik", "Raska", "Najveci centar u Srbiji")
        self.zla = _napravi_centar("Zlatibor", "Cajetina", "Planinski raj")
        self.stara = _napravi_centar("Stara planina", "Knjazevac", "Babin zub")
        _dodaj_ocenu(self.kop, 5)
        _dodaj_ocenu(self.zla, 3)

    def test_lista_prikazuje_sve_centre(self):
        resp = self.client.get(self.lista_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'ski_center/skiCentersList.html')
        self.assertEqual(len(resp.context['ski_centri']), 3)
        self.assertContains(resp, "Kopaonik")
        self.assertContains(resp, "Zlatibor")

    def test_pretraga_po_nazivu(self):
        resp = self.client.get(self.lista_url, {'q': 'Kopa'})
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi, ["Kopaonik"])

    def test_pretraga_po_lokaciji(self):
        resp = self.client.get(self.lista_url, {'q': 'Cajetina'})
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi, ["Zlatibor"])

    def test_pretraga_po_opisu(self):
        resp = self.client.get(self.lista_url, {'q': 'Babin'})
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi, ["Stara planina"])

    def test_sort_naziv_rastuce(self):
        resp = self.client.get(self.lista_url, {'sort': 'naziv_asc'})
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi, ["Kopaonik", "Stara planina", "Zlatibor"])

    def test_sort_naziv_opadajuce(self):
        resp = self.client.get(self.lista_url, {'sort': 'naziv_desc'})
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi, ["Zlatibor", "Stara planina", "Kopaonik"])

    def test_sort_ocena_opadajuce(self):
        resp = self.client.get(self.lista_url, {'sort': 'ocena_desc'})
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi[0], "Kopaonik")

    def test_javni_detalj_prikazuje_staze_i_zicare(self):
        Slope.objects.create(ski_center=self.kop, name="Karaman greben",
                             length_km=3.5, difficulty="crvena", status="otvorena")
        Lift.objects.create(ski_center=self.kop, name="Gvozdac", status="aktivna")
        url = reverse('ski_centar_detalj', args=[self.kop.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'ski_center/skiCenterPublicProfile.html')
        self.assertContains(resp, "Karaman greben")
        self.assertContains(resp, "Gvozdac")

    def test_pretraga_bez_rezultata(self):
        resp = self.client.get(self.lista_url, {'q': 'NePostoji123'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['ski_centri']), 0)

    def test_nevazeci_sort_ne_pada(self):
        resp = self.client.get(self.lista_url, {'sort': 'besmislica'})
        self.assertEqual(resp.status_code, 200)
        nazivi = [c.business_profile.business_name for c in resp.context['ski_centri']]
        self.assertEqual(nazivi, ["Kopaonik", "Stara planina", "Zlatibor"])

    def test_detalj_nepostojeceg_centra_404(self):
        url = reverse('ski_centar_detalj', args=[999999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
