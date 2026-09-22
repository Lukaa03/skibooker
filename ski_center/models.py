from django.db import models
from accounts.models import BusinessProfile

class SkiCenterProfile(models.Model):
    """
    Profil ski centra.

    Atributi:   business_profile: Veza sa poslovnim profilom (1-1).
                description: Opis ski centra.
                contact_phone: Kontakt telefon.
                contact_email: Kontakt email.
                website: URL zvaničnog sajta.
                photo: Fotografija ski centra (opciono).
    """
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    business_profile = models.OneToOneField(BusinessProfile, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    photo = models.ImageField(upload_to='ski_center_photos/', blank=True, null=True)
    class Meta:
        db_table = 'ski_center_profile'

    def __str__(self):
        return self.business_profile.business_name


class Slope(models.Model):
    """
    Staza u ski centru.

    Atributi:   ski_center: Ski centar kome staza pripada.
                name: Naziv staze.
                length_km: Dužina staze u kilometrima.
                difficulty: Težina staze (plava, crvena, crna).
                status: Status staze (otvorena, zatvorena).
    """
    DIFFICULTY_CHOICES = [
        ('plava', 'Plava'),
        ('crvena', 'Crvena'),
        ('crna', 'Crna'),
    ]
    STATUS_CHOICES = [
        ('otvorena', 'Otvorena'),
        ('zatvorena', 'Zatvorena'),
    ]
    ski_center = models.ForeignKey(SkiCenterProfile, on_delete=models.CASCADE, related_name='slopes')
    name = models.CharField(max_length=100)
    length_km = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='otvorena')

    class Meta:
        db_table = 'slope'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Lift(models.Model):
    """
    Žičara u ski centru.

    Atributi:   ski_center: Ski centar kome žičara pripada.
                name: Naziv žičare.
                status: Status žičare (aktivna, neaktivna).
    """
    STATUS_CHOICES = [
        ('aktivna', 'Aktivna'),
        ('neaktivna', 'Neaktivna'),
    ]
    ski_center = models.ForeignKey(SkiCenterProfile, on_delete=models.CASCADE, related_name='lifts')
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktivna')

    class Meta:
        db_table = 'lift'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
