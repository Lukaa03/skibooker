from .models import BusinessProfile

def user_profile(request):
    """
    Vraca tip prijavljenog poslovnog korisnika za sve template- ove.

    :model:`accounts.BusinessProfile`

    Argumenti : request - HTTP zahtev trenutnog korinsika

    return : Dict sa ključem 'user_business_type' koji sadrži tip prijavljenog poslovnog
             korisnika ili None ako korisnik nije prijavljen ili nije poslovni korisnik.

    """
    if request.user.is_authenticated:
        try:
            bp = BusinessProfile.objects.get(user=request.user)
            return {'user_business_type': bp.business_type}
        except BusinessProfile.DoesNotExist:
            pass
    return {'user_business_type': None}