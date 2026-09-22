from django.db import models
from accounts.models import BusinessProfile, ClientProfile

class InstructorProfile(models.Model):
    """
    Profil instruktora skijanja (ili snowborda).

    Atributi:   business_profile - veza sa poslovnim profilom (1-1).
                ski_center - ski centar kom instruktor pripada (opciono).
                ski_school - ski škola kojoj instruktor pripada (opciono).
                price_per_hour - cena casa u RSD.
                years_of_experience - godine iskustva.
                bio - kratak opis instruktora i casova.
                specialization - specijalizacija (freeride, snowboard, pocetnici,..)
                languages - jezici koje instruktor govori.
                qualifications - kvalifikacije i sertifikati
                photo - profilna fotografija instruktora.
    """

    SPECIALIZATION_CHOICES = [
        ('freeride', 'Freeride'),  ('pocetnici', 'Početnička nastava'),
        ('snowboard', 'Snowboard'), ('napredna', 'Napredna tehnika'),
    ]
    business_profile = models.OneToOneField(BusinessProfile, on_delete=models.CASCADE)
    ski_center = models.ForeignKey('ski_center.SkiCenterProfile', on_delete=models.SET_NULL, null=True, blank=True)
    ski_school = models.ForeignKey('ski_school.SkiSchoolProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='instructors')
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    years_of_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, blank=True, null=True)
    languages = models.CharField(max_length=200, blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='instructor_photos/', blank=True, null=True)

    class Meta:
        db_table = 'instructor_profile'

    def __str__(self):
        return self.business_profile.user.get_full_name()


class TimeSlot(models.Model):
    """
    Slobodan termin instruktora dostupan za rezervaciju.

    Atributi:   instructor - instruktor ciji je termin.
                date - datum termina.
                start_time - vreme pocetka termina.
                end_time - vreme zavrsetka termina.
                is_booked - da li je termin popunjen.

    """
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        db_table = 'time_slot'

    def __str__(self):
        return f"{self.instructor} - {self.date} {self.start_time}"


class Booking(models.Model):
    """
    Rezervacije ski casa izmedji instruktora i klijenta.

    Atributi:   client - klijent koji je napravio rezervaciju.
                time_slot - termin koji je rezervisan (1-1).
                status - status rezervacije (ceka potvrdu, potvrdjena, otkazana, realizovana ).
                reject_reason - razlog odbijanja rezervacije (opciono).
                created_at - datum i vreme kreiranja rezervacije .
    """

    STATUS_CHOICES = [
        ('ceka_potvrdu', 'Čeka potvrdu'), ('potvrdjena', 'Potvrđena'),
        ('realizovana', 'Realizovana'), ('otkazana', 'Otkazana'), ('odbijena', 'Odbijena'),
    ]
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='bookings')
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ceka_potvrdu')
    reject_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking'

    def __str__(self):
        return f"{self.client} - {self.time_slot}"