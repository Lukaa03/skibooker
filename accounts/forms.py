from django import forms
from django.contrib.auth.models import User


class RegistrationForm(forms.Form):
    """
    Forma za registraciju klijenta.

    Polja:  first_name - ime klijenta
            last_name - prezime klijenta
            email - email klijenta, mora biti jedinstvena u sistemu
            password - lozinka
            confirm_password - potvrda lozinke

    """
    first_name = forms.CharField(max_length=30, label='First name')
    last_name = forms.CharField(max_length=30, label='Last name')
    email = forms.EmailField(label='Email address')
    password = forms.CharField(widget=forms.PasswordInput, label='Password', min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm password')

    def clean(self):
        """
        Proverava jedinstvenost email adrese i preklapanje lozinki.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')

        if password and confirm and password != confirm:
            raise forms.ValidationError('Šifre se ne poklapaju.')

        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Već postoji nalog sa unetom email adresom.')

        return cleaned_data


class BusinessRegistrationForm(forms.Form):
    """
    Forma za validaciju poslovnog korisnika.

    Polja : first_name - Ime (obavezno samo za tip instruktor)
            last_name - prezime (obavezno samo za tip instruktor)
            email - email adresa, mora biti jedinstvena u sistemu
            password - lozinka, minimalno 8 karaktera
            confirm_password - potvrda lozinke
            business_type - tip poslovnog korinsika
            business_name - ime firme (obavezno za sve tipove, osim za instruktora)
            location - lokacija gde se nalazi biznis
    """
    BUSINESS_TYPE_CHOICES = [
        ('', 'Izaberi tip...'),
        ('ski_center', 'Ski centar'),
        ('rental', 'Rental firma'),
        ('ski_skola', 'Ski škola'),
        ('instructor', 'Instruktor'),
    ]

    first_name = forms.CharField(max_length=30, label='Ime', required=False)
    last_name = forms.CharField(max_length=30, label='Prezime', required=False)
    email = forms.EmailField(label='Email adresa')
    password = forms.CharField(widget=forms.PasswordInput, label='Lozinka', min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Potvrdi lozinku')
    business_type = forms.ChoiceField(choices=BUSINESS_TYPE_CHOICES, label='Tip poslovnog subjekta')
    business_name = forms.CharField(max_length=80, label='Naziv firme / Ime i prezime', required=False)
    location = forms.CharField(max_length=120, label='Ski centar (lokacija)', required=False)

    def clean_email(self):
        """
        Proverava jedinstvenost email adrese u sistemu.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email adresa je već registrovana.')
        return email

    def clean(self):
        """
        Proverava poklapanje lozinki i da li su popunjena obavezna polja (prema tipu korisnika).
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Lozinke se ne poklapaju.')
        business_type = cleaned_data.get('business_type')
        if not business_type:
            raise forms.ValidationError('Izaberi tip poslovnog subjekta.')
        if business_type == 'instructor':
            if not cleaned_data.get('first_name'):
                self.add_error('first_name', 'Ime je obavezno za instruktore.')
            if not cleaned_data.get('last_name'):
                self.add_error('last_name', 'Prezime je obavezno za instruktore.')
        else:
            if not cleaned_data.get('business_name'):
                self.add_error('business_name', 'Naziv firme je obavezan.')
        if business_type == 'ski_cener' and not cleaned_data.get('location'):
            self.add_error('location', 'Lokacija ski centra je obavezna.')
        return cleaned_data

class LoginForm(forms.Form):
    """
    Forma za prijavu vec postojećeg korisnika u sistem (i klijenta i poslovnog korisnika).
    Validacija podataka vrši se u viewu.

    Polja : email - email adresa korisnika, jedinstvena u sistemu.
            password - lozinka korinsika.
    """
    email = forms.EmailField(label='Email adresa')
    password = forms.CharField( widget=forms.PasswordInput, label='Lozinka')