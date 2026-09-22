"""
Seed skripta za punjenje baze SkiBooker aplikacije.
Pokretanje: python3 seed_baza.py (iz webapp/ foldera, dok manage.py postoji tu)

Kreira:
  - 2 ski centra
  - 1 ski skola
  - 3 instruktora (sa terminima)
  - 2 rental firme (sa opremom i varijantama)
  - 5 klijenata
  - rezervacije opreme i termina
  - recenzije
"""

import os
import sys
import django
from datetime import date, time, timedelta
from decimal import Decimal

# Django setup
HERE = os.path.dirname(os.path.abspath(__file__))
WEBAPP = '/Users/kristinapavlovic/project_SnowTech/webapp'
sys.path.insert(0, WEBAPP)
os.chdir(WEBAPP)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skibooker_webapp.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import ClientProfile, BusinessProfile
from ski_center.models import SkiCenterProfile, Slope, Lift
from instructor.models import InstructorProfile, TimeSlot, Booking
from rental.models import (
    RentalProfile, Equipment, EquipmentVariant,
    EquipmentReservation, Brand, EquipmentCategory
)
from ski_school.models import SkiSchoolProfile
from reviews.models import Review

def get_or_create_user(username, email, password, first_name='', last_name=''):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        }
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"  ✓ Kreiran korisnik: {email}")
    else:
        print(f"  · Postoji korisnik: {email}")
    return user


def seed():
    print("\n=== SEED BAZE ===\n")
    today = date.today()

    # ==========================================
    # KLIJENTI
    # ==========================================
    print(">> Klijenti")
    klijenti_data = [
        ('ana@test.com', 'Ana', 'Jović'),
        ('maja@test.com', 'Maja', 'Stojanović'),
        ('jovana@test.com', 'Jovana', 'Nikolić'),
        ('milica@test.com', 'Milica', 'Petrović'),
        ('jelena@test.com', 'Jelena', 'Marković'),
    ]
    klijenti = []
    for email, ime, prezime in klijenti_data:
        u = get_or_create_user(email, email, 'test1234', ime, prezime)
        cp, _ = ClientProfile.objects.get_or_create(user=u)
        klijenti.append(cp)

    # ==========================================
    # SKI CENTRI
    # ==========================================
    print("\n>> Ski centri")
    sc1_user = get_or_create_user('kopaonik_sc@test.com', 'kopaonik_sc@test.com', 'test1234', 'Ski', 'Kopaonik')
    sc1_bp, _ = BusinessProfile.objects.get_or_create(
        user=sc1_user,
        defaults={'business_type': 'ski_center', 'business_name': 'Ski Centar Kopaonik', 'location': 'Kopaonik'}
    )
    sc1, _ = SkiCenterProfile.objects.get_or_create(
        business_profile=sc1_bp,
        defaults={
            'description': 'Najveći ski centar u Srbiji sa 55 staza i 23 žičare.',
            'contact_phone': '036123456',
            'contact_email': 'info@kopaonik.rs',
            'website': 'https://www.skijalistasrbije.rs',
            'latitude': Decimal('43.2897'),
            'longitude': Decimal('20.8106'),
        }
    )
    print(f"  ✓ Ski centar: Kopaonik (pk={sc1.pk})")

    sc2_user = get_or_create_user('jahorina_sc@test.com', 'jahorina_sc@test.com', 'test1234', 'Ski', 'Jahorina')
    sc2_bp, _ = BusinessProfile.objects.get_or_create(
        user=sc2_user,
        defaults={'business_type': 'ski_center', 'business_name': 'Ski Centar Jahorina', 'location': 'Jahorina'}
    )
    sc2, _ = SkiCenterProfile.objects.get_or_create(
        business_profile=sc2_bp,
        defaults={
            'description': 'Olimpijski ski centar Jahorina.',
            'contact_phone': '057123456',
            'contact_email': 'info@jahorina.com',
            'latitude': Decimal('43.7167'),
            'longitude': Decimal('18.5667'),
        }
    )
    print(f"  ✓ Ski centar: Jahorina (pk={sc2.pk})")

    # Staze Kopaonik
    staze_kopaonik = [
        ('Sunčana dolina', 'plava', Decimal('3.5'), 'otvorena'),
        ('Crni Vrh', 'crna', Decimal('2.1'), 'otvorena'),
        ('Karaman Greben', 'crvena', Decimal('4.2'), 'otvorena'),
        ('Mali Karaman', 'plava', Decimal('1.8'), 'zatvorena'),
    ]
    for naziv, tezina, duzina, status in staze_kopaonik:
        Slope.objects.get_or_create(
            ski_center=sc1, name=naziv,
            defaults={'difficulty': tezina, 'length_km': duzina, 'status': status}
        )
    print(f"  ✓ Kreirane staze za Kopaonik")

    # Žičare Kopaonik
    zicare_kopaonik = [
        ('Šetka', 'aktivna'),
        ('Suvo Rudište', 'aktivna'),
        ('Pančićev Vrh', 'neaktivna'),
    ]
    for naziv, status in zicare_kopaonik:
        Lift.objects.get_or_create(ski_center=sc1, name=naziv, defaults={'status': status})
    print(f"  ✓ Kreirane žičare za Kopaonik")

    # Staze Jahorina
    staze_jahorina = [
        ('Olimpijska', 'crvena', Decimal('2.9'), 'otvorena'),
        ('Rajska dolina', 'plava', Decimal('1.5'), 'otvorena'),
    ]
    for naziv, tezina, duzina, status in staze_jahorina:
        Slope.objects.get_or_create(
            ski_center=sc2, name=naziv,
            defaults={'difficulty': tezina, 'length_km': duzina, 'status': status}
        )

    # ==========================================
    # SKI SKOLA
    # ==========================================
    print("\n>> Ski škola")
    ss_user = get_or_create_user('kopaonik_school@test.com', 'kopaonik_school@test.com', 'test1234', 'Ski', 'Škola')
    ss_bp, _ = BusinessProfile.objects.get_or_create(
        user=ss_user,
        defaults={'business_type': 'ski_skola', 'business_name': 'Ski Škola Kopaonik', 'location': 'Kopaonik'}
    )
    try:
        ss, _ = SkiSchoolProfile.objects.get_or_create(
            business_profile=ss_bp,
            defaults={
                'ski_center': sc1,
                'description': 'Profesionalna ski škola na Kopaoniku.',
                'contact_phone': '036111222',
                'contact_email': 'skola@kopaonik.rs',
            }
        )
        print(f"  ✓ Ski škola: Kopaonik (pk={ss.pk})")
    except Exception as e:
        ss = None
        print(f"  ⚠ Ski škola nije kreirana: {e}")

    # ==========================================
    # INSTRUKTORI
    # ==========================================
    print("\n>> Instruktori")
    instruktori_data = [
        ('marko.instruktor@test.com', 'Marko', 'Marković', 'freeride', 'srpski, engleski', 8, 3500),
        ('ivana.instructor@test.com', 'Ivana', 'Đurić', 'alpsko skijanje', 'srpski, nemački', 5, 2800),
        ('jovana.instructor@test.com', 'Jovana', 'Milosavljević', 'snowboard', 'srpski, engleski', 3, 2500),
    ]
    instruktori = []
    for email, ime, prezime, spec, jezici, godine, cena in instruktori_data:
        u = get_or_create_user(email, email, 'test1234', ime, prezime)
        bp, _ = BusinessProfile.objects.get_or_create(
            user=u,
            defaults={
                'business_type': 'instructor',
                'business_name': f'{ime} {prezime}',
                'location': 'Kopaonik'
            }
        )
        instr, _ = InstructorProfile.objects.get_or_create(
            business_profile=bp,
            defaults={
                'ski_center': sc1,
                'ski_school': ss,
                'specialization': spec,
                'languages': jezici,
                'years_of_experience': godine,
                'price_per_hour': Decimal(str(cena)),
                'qualifications': 'ISIA sertifikat',
                'bio': f'Iskusni instruktor sa {godine} godina iskustva.',
            }
        )
        instruktori.append(instr)
        print(f"  ✓ Instruktor: {ime} {prezime} (pk={instr.pk})")

    # Termini za instruktore
    print("  >> Termini")
    for instr in instruktori:
        for delta in range(1, 8):
            datum = today + timedelta(days=delta)
            for sat_pocetak, sat_kraj in [('09:00', '10:00'), ('11:00', '12:00'), ('14:00', '15:00')]:
                TimeSlot.objects.get_or_create(
                    instructor=instr,
                    date=datum,
                    start_time=sat_pocetak,
                    defaults={'end_time': sat_kraj, 'is_booked': False}
                )
    print(f"  ✓ Kreirani termini za {len(instruktori)} instruktora")

    # Jedna rezervacija termina (za testiranje SSU_05)
    slobodan_termin = TimeSlot.objects.filter(instructor=instruktori[0], is_booked=False).first()
    if slobodan_termin and not hasattr(slobodan_termin, 'booking'):
        try:
            Booking.objects.get_or_create(
                time_slot=slobodan_termin,
                defaults={
                    'client': klijenti[0],
                    'status': 'ceka_potvrdu'
                }
            )
            slobodan_termin.is_booked = True
            slobodan_termin.save()
            print(f"  ✓ Kreirana rezervacija termina")
        except Exception as e:
            print(f"  ⚠ Rezervacija termina: {e}")

    # ==========================================
    # RENTAL FIRME
    # ==========================================
    print("\n>> Rental firme")

    r1_user = get_or_create_user('alpski_rental@test.com', 'alpski_rental@test.com', 'test1234', 'Alpski', 'Rental')
    r1_bp, _ = BusinessProfile.objects.get_or_create(
        user=r1_user,
        defaults={'business_type': 'rental', 'business_name': 'Alpski Rental', 'location': 'Kopaonik'}
    )
    r1, _ = RentalProfile.objects.get_or_create(
        business_profile=r1_bp,
        defaults={
            'ski_center': sc1,
            'description': 'Vrhunska oprema za skijanje i snowboard.',
            'contact_phone': '036987654',
            'contact_email': 'info@alpski-rental.rs',
        }
    )
    print(f"  ✓ Rental: Alpski Rental (pk={r1.pk})")

    r2_user = get_or_create_user('skirent_kopaonik@test.com', 'skirent_kopaonik@test.com', 'test1234', 'SkiRent', 'Kopaonik')
    r2_bp, _ = BusinessProfile.objects.get_or_create(
        user=r2_user,
        defaults={'business_type': 'rental', 'business_name': 'SkiRent Kopaonik', 'location': 'Kopaonik'}
    )
    r2, _ = RentalProfile.objects.get_or_create(
        business_profile=r2_bp,
        defaults={
            'ski_center': sc1,
            'description': 'Povoljno iznajmljivanje ski opreme.',
            'contact_phone': '036111333',
            'contact_email': 'info@skirent.rs',
        }
    )
    print(f"  ✓ Rental: SkiRent Kopaonik (pk={r2.pk})")

    # Brendovi i kategorije
    brendovi = {}
    for naziv in ['Atomic', 'Rossignol', 'Burton', 'Salomon', 'Head']:
        b, _ = Brand.objects.get_or_create(name=naziv)
        brendovi[naziv] = b

    kategorije = {}
    for naziv in ['Skije', 'Snowboard', 'Cipele', 'Kaciga', 'Štapovi']:
        k, _ = EquipmentCategory.objects.get_or_create(name=naziv)
        kategorije[naziv] = k

    # Oprema za Alpski Rental
    oprema_r1 = [
        (brendovi['Atomic'], 'Redster X9', kategorije['Skije'], Decimal('2500')),
        (brendovi['Burton'], 'Custom X', kategorije['Snowboard'], Decimal('2200')),
        (brendovi['Rossignol'], 'Experience 80', kategorije['Skije'], Decimal('1800')),
        (brendovi['Salomon'], 'Icon LT', kategorije['Kaciga'], Decimal('600')),
        (brendovi['Salomon'], 'X Pro 130', kategorije['Cipele'], Decimal('1200')),
    ]
    equipments_r1 = []
    for brend, model, kat, cena in oprema_r1:
        eq, _ = Equipment.objects.get_or_create(
            rental=r1, brand=brend, model=model,
            defaults={'category': kat, 'price_per_day': cena, 'is_active': True,
                      'description': f'{brend.name} {model} - vrhunska oprema.'}
        )
        equipments_r1.append(eq)

    # Oprema za SkiRent
    oprema_r2 = [
        (brendovi['Atomic'], 'Redster X9', kategorije['Skije'], Decimal('1500')),
        (brendovi['Burton'], 'Custom X', kategorije['Snowboard'], Decimal('2200')),
        (brendovi['Rossignol'], 'Experience 80', kategorije['Skije'], Decimal('1800')),
        (brendovi['Salomon'], 'Icon LT', kategorije['Kaciga'], Decimal('600')),
        (brendovi['Salomon'], 'X Pro 130', kategorije['Cipele'], Decimal('1200')),
    ]
    equipments_r2 = []
    for brend, model, kat, cena in oprema_r2:
        eq, _ = Equipment.objects.get_or_create(
            rental=r2, brand=brend, model=model,
            defaults={'category': kat, 'price_per_day': cena, 'is_active': True}
        )
        equipments_r2.append(eq)

    print(f"  ✓ Kreirana oprema za obe rental firme")

    # Varijante opreme
    velicine_skije = ['160cm', '165cm', '170cm', '175cm', '180cm']
    velicine_snowboard = ['148cm', '152cm', '156cm', '160cm']
    velicine_cipele = ['38', '39', '40', '41', '42', '43', '44', '45']
    velicine_kaciga = ['S', 'M', 'L', 'XL']

    def dodaj_varijante(eq, velicine, kolicina=3):
        for vel in velicine:
            EquipmentVariant.objects.get_or_create(
                equipment=eq, size=vel,
                defaults={'quantity': kolicina}
            )

    for eq in equipments_r1 + equipments_r2:
        if eq.category.name == 'Skije':
            dodaj_varijante(eq, velicine_skije)
        elif eq.category.name == 'Snowboard':
            dodaj_varijante(eq, velicine_snowboard)
        elif eq.category.name == 'Cipele':
            dodaj_varijante(eq, velicine_cipele)
        else:
            dodaj_varijante(eq, velicine_kaciga)

    print(f"  ✓ Kreirane varijante opreme")

    # ==========================================
    # REZERVACIJE OPREME
    # ==========================================
    print("\n>> Rezervacije opreme")

    # Uzmi prvu varijantu prve opreme (Atomic Redster X9 - Alpski Rental)
    prva_varijanta = EquipmentVariant.objects.filter(
        equipment=equipments_r1[0]
    ).first()

    rezervacije_data = [
        (klijenti[0], prva_varijanta, today + timedelta(days=2), today + timedelta(days=5), 'ceka_potvrdu'),
        (klijenti[1], prva_varijanta, today + timedelta(days=7), today + timedelta(days=10), 'potvrdjena'),
        (klijenti[2], prva_varijanta, today - timedelta(days=10), today - timedelta(days=7), 'realizovana'),
        (klijenti[3], prva_varijanta, today + timedelta(days=1), today + timedelta(days=3), 'ceka_potvrdu'),
    ]

    for klijent, varijanta, start, end, status in rezervacije_data:
        EquipmentReservation.objects.get_or_create(
            client=klijent,
            equipment_variant=varijanta,
            start_date=start,
            defaults={
                'end_date': end,
                'quantity': 1,
                'status': status,
            }
        )
    print(f"  ✓ Kreirane rezervacije opreme")

    # ==========================================
    # OCENE (REVIEWS)
    # ==========================================
    print("\n>> Ocene")

    # Ocene za ski centre
    ocene_sci_centar = [
        (klijenti[0], sc1, 5, 'Odličan ski centar, preporučujem svima!'),
        (klijenti[1], sc1, 4, 'Lepe staze, malo gužve vikendom.'),
        (klijenti[2], sc1, 5, 'Fantastično iskustvo, jedva čekam sledeću sezonu.'),
        (klijenti[3], sc2, 4, 'Jahorina je uvek posebna, divne staze.'),
        (klijenti[4], sc2, 3, 'Dobro, ali moglo bi bolje sa žičarama.'),
    ]
    for klijent, centar, ocena, komentar in ocene_sci_centar:
        Review.objects.get_or_create(
            reviewer=klijent,
            ski_center=centar,
            defaults={'rating': ocena, 'comment': komentar, 'is_removed': False}
        )
    print(f"  ✓ Ocene za ski centre")

    # Ocene za instruktore
    ocene_instruktori = [
        (klijenti[0], instruktori[0], 5, 'Marko je odličan instruktor, strpljiv i profesionalan.'),
        (klijenti[1], instruktori[0], 4, 'Vrlo dobar, naučila sam puno za kratko vreme.'),
        (klijenti[2], instruktori[1], 5, 'Ivana je fantastična, toplo preporučujem!'),
        (klijenti[3], instruktori[1], 4, 'Profesionalna i ljubazna.'),
        (klijenti[4], instruktori[2], 5, 'Snowboard čas sa Jovanom je bio sjajan!'),
        (klijenti[0], instruktori[2], 3, 'Solidno, ali očekivala sam više.'),
    ]
    for klijent, instruktor, ocena, komentar in ocene_instruktori:
        Review.objects.get_or_create(
            reviewer=klijent,
            instructor=instruktor,
            defaults={'rating': ocena, 'comment': komentar, 'is_removed': False}
        )
    print(f"  ✓ Ocene za instruktore")

    # Ocene za rental firme
    realizovana_rez = EquipmentReservation.objects.filter(status='realizovana').first()
    ocene_rental = [
        (klijenti[0], r1, realizovana_rez, 4, 'Oprema je bila u odličnom stanju.'),
        (klijenti[1], r1, None, 5, 'Brza usluga i kvalitetna oprema!'),
        (klijenti[2], r2, None, 4, 'Povoljne cene, dobra oprema.'),
        (klijenti[3], r2, None, 3, 'Prosečno, ali za cenu je ok.'),
    ]
    for klijent, rental, rezervacija, ocena, komentar in ocene_rental:
        Review.objects.get_or_create(
            reviewer=klijent,
            rental=rental,
            defaults={
                'rating': ocena,
                'comment': komentar,
                'reservation': rezervacija,
                'is_removed': False
            }
        )
    print(f"  ✓ Ocene za rental firme")

    # ==========================================
    # SUMMARY
    # ==========================================
    print("\n=== SEED ZAVRŠEN ===")
    print(f"  Korisnici: {User.objects.count()}")
    print(f"  Klijenti: {ClientProfile.objects.count()}")
    print(f"  Ski centri: {SkiCenterProfile.objects.count()}")
    print(f"  Instruktori: {InstructorProfile.objects.count()}")
    print(f"  Termini: {TimeSlot.objects.count()}")
    print(f"  Rental firme: {RentalProfile.objects.count()}")
    print(f"  Oprema: {Equipment.objects.count()}")
    print(f"  Varijante: {EquipmentVariant.objects.count()}")
    print(f"  Rezervacije opreme: {EquipmentReservation.objects.count()}")
    print(f"  Ocene: {Review.objects.count()}")
    print()
    print("Nalozi za testiranje (lozinka: test1234):")
    print("  Klijent:       ana@test.com")
    print("  Rental firma:  alpski_rental@test.com")
    print("  Ski centar:    kopaonik_sc@test.com")
    print("  Instruktor:    marko.instruktor@test.com")
    print("  Ski škola:     kopaonik_school@test.com")


if __name__ == '__main__':
    seed()
