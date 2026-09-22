from django.db import models
from accounts.models import ClientProfile
from instructor.models import InstructorProfile, Booking
from ski_center.models import SkiCenterProfile
from rental.models import RentalProfile, EquipmentReservation

class Review(models.Model):
    reviewer = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_removed = models.BooleanField(default=False)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    ski_center = models.ForeignKey(SkiCenterProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    rental = models.ForeignKey(RentalProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    reservation = models.ForeignKey(EquipmentReservation, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'review'

    def __str__(self):
        target = self.instructor or self.ski_center or self.rental or 'nepoznato'
        return f'{self.reviewer} - {target} ({self.rating}/5)'

    @property
    def stars_range(self):
        return range(self.rating)