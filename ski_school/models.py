from django.db import models
from accounts.models import BusinessProfile
from ski_center.models import SkiCenterProfile

class SkiSchoolProfile(models.Model):
    business_profile = models.OneToOneField(BusinessProfile, on_delete=models.CASCADE)
    ski_center = models.ForeignKey(SkiCenterProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='ski_schools')
    description = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    class Meta:
        db_table = 'ski_school_profile'

    def __str__(self):
        return self.business_profile.business_name