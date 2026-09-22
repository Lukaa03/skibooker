from django import forms

class InstructorProfileForm(forms.Form):
    """
    Forma za azuriranje profila instruktora.

    Polja:  first_name - ime instruktora (obavezno).
            last_name - prezime instruktora (obavezno).
            specialization - specijalizacija (freeride, snowboard,..) (opciono).
            price_per_hour - cena casa  u RSD (mora biti pozitivan broj).
            years_of_experience - godine iskustva (mora biti pozitivan broj).
            languages - jezici koje instruktor govori (opciono).
            bio - kratak opis instruktora i casova (opciono).
            qualifications - kvalifikacije i sertifikati (opciono).
            photo - profilna fotografija instruktora (opciono).
    """
    first_name = forms.CharField(max_length=50, error_messages={'required': 'Ime je obavezno.'})
    last_name = forms.CharField(max_length=50, error_messages={'required': 'Prezime je obavezno.'})
    specialization = forms.CharField(required=False)
    price_per_hour = forms.DecimalField(
        min_value=0,
        error_messages={
            'min_value': 'Cena časa ne može biti negativna.',
            'invalid': 'Unesite ispravan broj.'
        }
    )
    years_of_experience = forms.IntegerField(
        min_value=0,
        error_messages={
            'min_value': 'Godine iskustva ne mogu biti negativne.',
            'invalid': 'Unesite ispravan broj.'
        }
    )
    languages = forms.CharField(required=False)
    bio = forms.CharField(required=False)
    qualifications = forms.CharField(required=False)
    photo = forms.ImageField(required=False)