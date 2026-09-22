from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from accounts.models import BusinessProfile
from instructor.models import InstructorProfile, Booking
from reviews.models import Review
from .models import SkiSchoolProfile

@login_required
def ski_school_profile(request):
    bp = get_object_or_404(BusinessProfile, user=request.user)
    school = get_object_or_404(SkiSchoolProfile, business_profile=bp)

    instructors = list(InstructorProfile.objects.filter(ski_school=school).select_related('business_profile__user'))
    for ins in instructors:
        ins.avg_rating = ins.reviews.filter(is_removed=False).aggregate(Avg('rating'))['rating__avg']

    school_avg = Review.objects.filter(instructor__ski_school=school, is_removed=False).aggregate(Avg('rating'))['rating__avg']

    bookings = Booking.objects.filter(time_slot__instructor__ski_school=school).select_related('client__user', 'time_slot__instructor__business_profile__user').order_by('-created_at')

    instructor_filter = request.GET.get('instructor', '')
    status_filter = request.GET.get('status', '')
    if instructor_filter:
        bookings = bookings.filter(time_slot__instructor__pk=instructor_filter)
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'ski_school/skiSchoolProfile.html', {
        'school': school,
        'instructors': instructors,
        'bookings': bookings,
        'school_avg': school_avg,
        'instructor_filter': instructor_filter,
        'status_filter': status_filter,
    })