"""
Seed skripta za SSU_05 (Rezervacija casa) — priprema podatke za Selenium testove.

Sta radi:
    - kreira (ili azurira) nekoliko instruktora: User + BusinessProfile + InstructorProfile
    - kreira jedan klijentski nalog za rucno testiranje
    - svakom instruktoru dodaje slobodne BUDUCE termine
    - OSLOBADJA vec rezervisane seed-termine (brise njihov Booking) da bi testovi bili ponovljivi
    - na kraju ispisuje proveru: instruktori i broj slobodnih buducih termina

Pokretanje (iz root foldera projekta):
    python crosstestovi/seed_ssu05.py

Nalog za prijavu (svi):  lozinka123
"""
import os
import sys
from datetime import time, timedelta

import django

# --- podesavanje Django okruzenja (webapp je pored crosstestovi/) ---
HERE = os.path.dirname(os.path.abspath(__file__))
WEBAPP = os.path.abspath(os.path.join(HERE, "..", "webapp"))
sys.path.insert(0, WEBAPP)
os.chdir(WEBAPP)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skibooker_webapp.settings")
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import BusinessProfile, ClientProfile
from instructor.models import InstructorProfile, TimeSlot, Booking
from ski_center.models import SkiCenterProfile, Slope, Lift

LOZINKA = "lozinka123"

INSTRUKTORI = [
    {"email": "instruktor1@skibooker.rs", "ime": "Marko", "prezime": "Skijic",
     "spec": "pocetnici", "cena": 3000, "iskustvo": 5, "lokacija": "Kopaonik"},
    {"email": "instruktor2@skibooker.rs", "ime": "Jovana", "prezime": "Boardic",
     "spec": "snowboard", "cena": 3500, "iskustvo": 8, "lokacija": "Zlatibor"},
]

# buduci dani (u odnosu na danas) za koje se prave termini
DANI = [2, 3, 4]
POCETAK = time(10, 0)
KRAJ = time(11, 0)


def uredi_korisnika(spec):
    """Kreira/azurira instruktora sa aktivnim nalogom i praznim slobodnim terminima."""
    user, _ = User.objects.get_or_create(
        username=spec["email"],
        defaults={"email": spec["email"], "first_name": spec["ime"], "last_name": spec["prezime"]},
    )
    user.email = spec["email"]
    user.first_name = spec["ime"]
    user.last_name = spec["prezime"]
    user.is_active = True
    user.set_password(LOZINKA)
    user.save()

    bp, _ = BusinessProfile.objects.get_or_create(
        user=user,
        defaults={"business_type": "instructor",
                  "business_name": f"{spec['ime']} {spec['prezime']}",
                  "location": spec["lokacija"]},
    )
    bp.business_type = "instructor"
    bp.location = spec["lokacija"]
    bp.save()

    instruktor, _ = InstructorProfile.objects.get_or_create(
        business_profile=bp,
        defaults={"price_per_hour": spec["cena"], "years_of_experience": spec["iskustvo"],
                  "specialization": spec["spec"]},
    )
    instruktor.price_per_hour = spec["cena"]
    instruktor.years_of_experience = spec["iskustvo"]
    instruktor.specialization = spec["spec"]
    instruktor.save()
    return instruktor


def dodaj_slobodne_termine(instruktor):
    danas = timezone.now().date()
    napravljeno = 0
    for d in DANI:
        datum = danas + timedelta(days=d)
        slot, kreiran = TimeSlot.objects.get_or_create(
            instructor=instruktor, date=datum, start_time=POCETAK,
            defaults={"end_time": KRAJ, "is_booked": False},
        )
        # oslobodi termin ako je iz prethodnog test-pokretanja ostao rezervisan
        Booking.objects.filter(time_slot=slot).delete()
        if slot.is_booked or slot.end_time != KRAJ:
            slot.is_booked = False
            slot.end_time = KRAJ
            slot.save()
        if kreiran:
            napravljeno += 1
    return napravljeno


def uredi_ski_centar():
    """
    Ski centar nalog za SSU_09 (upravljanje profilom ski centra).
    Kreira User + BusinessProfile + SkiCenterProfile + jednu stazu i zicaru.
    """
    email = "centar@skibooker.rs"
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": "Ski", "last_name": "Centar"},
    )
    user.is_active = True
    user.set_password(LOZINKA)
    user.save()
    bp, _ = BusinessProfile.objects.get_or_create(
        user=user,
        defaults={"business_type": "ski_center",
                  "business_name": "Ski Centar Kopaonik", "location": "Kopaonik"},
    )
    bp.business_type = "ski_center"
    bp.save()
    sc, _ = SkiCenterProfile.objects.get_or_create(
        business_profile=bp,
        defaults={"description": "Najveci ski centar u Srbiji",
                  "contact_email": "info@kopaonik.rs", "contact_phone": "011/123-456"},
    )
    Slope.objects.get_or_create(
        ski_center=sc, name="Karaman greben",
        defaults={"length_km": 3.5, "difficulty": "crvena", "status": "otvorena"},
    )
    Lift.objects.get_or_create(
        ski_center=sc, name="Gvozdac", defaults={"status": "aktivna"},
    )
    return email, sc.pk


def uredi_klijenta():
    """Klijentski nalog za rucno testiranje rezervacije."""
    email = "klijent@skibooker.rs"
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": "Test", "last_name": "Klijent"},
    )
    user.is_active = True
    user.set_password(LOZINKA)
    user.save()
    ClientProfile.objects.get_or_create(user=user)
    return email


def main():
    print("=== SEED SSU_05 ===")
    for spec in INSTRUKTORI:
        instruktor = uredi_korisnika(spec)
        n = dodaj_slobodne_termine(instruktor)
        print(f"  instruktor: {spec['email']}  (+{n} novih termina)")

    klijent = uredi_klijenta()
    print(f"  klijent:    {klijent}")

    centar_email, centar_pk = uredi_ski_centar()
    print(f"  ski centar: {centar_email}  (SkiCenterProfile pk={centar_pk})")

    # --- PROVERA ---
    danas = timezone.now().date()
    print("\n=== PROVERA (slobodni buduci termini) ===")
    ukupno_slobodnih = 0
    for instruktor in InstructorProfile.objects.select_related("business_profile__user"):
        slobodni = TimeSlot.objects.filter(
            instructor=instruktor, is_booked=False, date__gte=danas
        ).count()
        ukupno_slobodnih += slobodni
        ime = instruktor.business_profile.user.get_full_name()
        print(f"  {ime:<22} pk={instruktor.pk:<3} slobodnih buducih termina: {slobodni}")

    print(f"\n  UKUPNO slobodnih buducih termina: {ukupno_slobodnih}")
    if ukupno_slobodnih:
        print("  OK — Selenium legalni test SSU_05 sada ima sta da rezervise.")
    else:
        print("  UPOZORENJE — nema slobodnih termina, proveri seed.")
    print(f"\n  Prijava (svi nalozi): lozinka = {LOZINKA}")


if __name__ == "__main__":
    main()
