from django.db import models
from django.contrib.auth.models import User


class ClientProfile(models.Model):
    """
    Profil klijentskog korisnika.

    Atributi:   user - veza sa Django User modelom (1-1).
                phone - broj telefona korisnika.
                dateOfBirth - datum rodjenja korisnika.
                profilePhotoUrl - url profilne fotografije, opciono.

    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    dateOfBirth = models.DateField(blank=True, null=True)
    profilePhotoUrl = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'client_profile'

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class BusinessRequest(models.Model):
    """
    Zahtevi za poslovne profile, ceka se odobrenje admina.

    Atributi:   user - veza sa Django user modelom (1-1)
                business_type - tip poslovnog korisnika.
                business_name - naziv firme.
                location - lokacija poslovnog klijenta.
                status - status zahteva.
                created_at - datum i vreme kreiranja zahteva.
    """
    STATUS_CHOICES = [
        ('na_cekanju', 'Na čekanju'),
        ('odobreno', 'Odobreno'),
        ('odbijeno', 'Odbijeno'),
    ]

    BUSINESS_TYPE_CHOICES = [
        ('ski_center', 'Ski centar'),
        ('rental', 'Rental firma'),
        ('ski_skola', 'Ski škola'),
        ('instructor', 'Instruktor'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    business_name = models.CharField(max_length=80)
    location = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='na_cekanju')
    created_at = models.DateTimeField(auto_now_add=True)
    reject_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'business_request'

    def __str__(self):
        return f"{self.business_name} ({self.get_status_display()})"


class BusinessProfile(models.Model):
    """
    Profil odobrenog poslovnog korisnika.

    Atributi :  user - veza sa Django User modelom (1-1 )
                business_type- tip poslovnog korisnika.
                business_name - naziv firme ili ime i prezime korisnika.
                location - lokacija poslovnog korinsika.

    """
    BUSINESS_TYPE_CHOICES = [
        ('ski_center', 'Ski centar'),
        ('rental', 'Rental firma'),
        ('ski_skola', 'Ski škola'),
        ('instructor', 'Instruktor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    business_name = models.CharField(max_length=80)
    location = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        db_table = 'business_profile'

    def __str__(self):
        return f"{self.business_name} ({self.get_business_type_display()})"

class AdminLog(models.Model):
    """Evidencija administratorskih akcija (audit log)."""
    ACTION_CHOICES = [
        ('odobri_zahtev', 'Odobrio zahtev'),
        ('odbij_zahtev', 'Odbio zahtev'),
        ('ukloni_recenziju', 'Uklonio recenziju'),
        ('blokiraj', 'Blokirao nalog'),
    ]
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target = models.CharField(max_length=200, blank=True)   # nad cim je akcija (npr. naziv firme)
    details = models.TextField(blank=True, null=True)        # npr. razlog odbijanja
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%d.%m.%Y %H:%M} · {self.admin} · {self.get_action_display()} · {self.target}'