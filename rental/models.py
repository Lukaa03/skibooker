from django.db import models

from accounts.models import BusinessProfile, ClientProfile
from ski_center.models import SkiCenterProfile


class RentalProfile(models.Model):
    """
    Profil rental firme.

    Atributi:
        business_profile - veza sa BusinessProfile modelom (1-1).
        ski_center - ski centar kome rental firma pripada.
        description - opis firme.
        contact_phone - kontakt telefon.
        contact_email - kontakt email.
        website - web sajt firme.
        logo - url logotipa firme.
        average_rating - prosečna ocena firme.
    """

    business_profile = models.OneToOneField(
        BusinessProfile,
        on_delete=models.CASCADE
    )

    ski_center = models.ForeignKey(
        SkiCenterProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rentals'
    )

    description = models.TextField(blank=True, null=True)

    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    contact_email = models.EmailField(
        blank=True,
        null=True
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    logo = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )

    class Meta:
        db_table = 'rental_profile'

    def __str__(self):
        return self.business_profile.business_name


class EquipmentCategory(models.Model):
    """
    Kategorija opreme.

    Atributi:
        name - naziv kategorije.
        description - opis kategorije.
    """

    name = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'equipment_category'

    def __str__(self):
        return self.name


class Brand(models.Model):
    """
    Proizvođač opreme.

    Atributi:
        name - naziv proizvođača.
        description - opis proizvođača.
    """

    name = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'brand'

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """
    Model opreme.

    Jedan model opreme može imati više
    varijanti različitih veličina.

    Atributi:
        rental - rental firma kojoj oprema pripada.
        category - kategorija opreme.
        brand - proizvođač.
        model - naziv modela.
        description - opis opreme.
        price_per_day - cena iznajmljivanja po danu.
        image - url slike opreme.
        is_active - da li je oprema dostupna za prikaz.
        created_at - datum dodavanja.
    """

    rental = models.ForeignKey(
        RentalProfile,
        on_delete=models.CASCADE,
        related_name='equipment'
    )

    category = models.ForeignKey(
        EquipmentCategory,
        on_delete=models.PROTECT,
        related_name='equipment'
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='equipment'
    )

    model = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    price_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to='equipment_images/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'equipment'
        ordering = ['brand__name', 'model']

    def __str__(self):
        return f"{self.brand.name} {self.model}"


class EquipmentVariant(models.Model):
    """
    Varijanta opreme.

    Jedan model opreme može imati više
    različitih veličina.

    Atributi:
        equipment - model opreme.
        size - veličina opreme.
        quantity - raspoloživa količina.
    """

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    size = models.CharField(
        max_length=20
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        db_table = 'equipment_variant'
        unique_together = ('equipment', 'size')
        ordering = ['equipment', 'size']

    def __str__(self):
        return f"{self.equipment} ({self.size})"


class EquipmentReservation(models.Model):
    """
    Rezervacija opreme.

    Atributi:
        client - klijent koji rezerviše opremu.
        equipment_variant - rezervisana varijanta opreme.
        quantity - broj rezervisanih komada.
        start_date - datum početka rezervacije.
        end_date - datum završetka rezervacije.
        status - status rezervacije.
        reject_reason - razlog odbijanja rezervacije.
        created_at - datum i vreme kreiranja rezervacije.
    """

    STATUS_CHOICES = [
        ('ceka_potvrdu', 'Čeka potvrdu'),
        ('potvrdjena', 'Potvrđena'),
        ('realizovana', 'Realizovana'),
        ('otkazana', 'Otkazana'),
        ('odbijena', 'Odbijena'),
    ]

    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment_reservations'
    )

    equipment_variant = models.ForeignKey(
        EquipmentVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations'
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ceka_potvrdu'
    )

    reject_reason = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'equipment_reservation'
        ordering = ['-created_at']

    def __str__(self):
        client = str(self.client) if self.client else "Obrisan korisnik"
        equipment = str(self.equipment_variant) if self.equipment_variant else "Obrisana oprema"

        return f"{client} - {equipment}"