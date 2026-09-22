from django import forms

from .models import (
    Equipment,
    EquipmentVariant,
    EquipmentReservation
)

class EquipmentForm(forms.ModelForm):
    """
    Forma za dodavanje i izmenu modela opreme.
    """

    class Meta:
        model = Equipment

        fields = [
            'category',
            'brand',
            'model',
            'description',
            'price_per_day',
            'image',
            'is_active'
        ]

        labels = {
            'category': 'Kategorija',
            'brand': 'Brend',
            'model': 'Model',
            'description': 'Opis',
            'price_per_day': 'Cena po danu',
            'image': 'Slika',
            'is_active': 'Aktivna ponuda'
        }

    def clean_price_per_day(self):
        price = self.cleaned_data['price_per_day']

        if price <= 0:
            raise forms.ValidationError(
                'Cena mora biti veća od nule.'
            )

        return price



class EquipmentReservationForm(forms.ModelForm):
    """
    Forma za rezervaciju opreme.
    Korisnik bira: veličinu, količinu, datum od, datum do
    """

    class Meta:
        model = EquipmentReservation

        fields = [
            'equipment_variant',
            'quantity',
            'start_date',
            'end_date'
        ]

        labels = {
            'equipment_variant': 'Veličina',
            'quantity': 'Broj komada',
            'start_date': 'Datum od',
            'end_date': 'Datum do'
        }

        widgets = {
            'equipment_variant': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'min': 1
                }
            ),
            'start_date': forms.DateInput(
                attrs={
                    'class': 'form-input',
                    'type': 'date'
                }
            ),
            'end_date': forms.DateInput(
                attrs={
                    'class': 'form-input',
                    'type': 'date'
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        if start and end and end < start:
            raise forms.ValidationError(
                'Datum završetka mora biti nakon datuma početka.'
            )

        return cleaned_data


class RejectReservationForm(forms.Form):
    """
    Forma za unos razloga odbijanja rezervacije.
    """

    reject_reason = forms.CharField(
        label='Razlog odbijanja',
        widget=forms.Textarea,
        error_messages={
            'required': 'Unesite razlog odbijanja.'
        }
    )


class EquipmentVariantForm(forms.ModelForm):

    class Meta:

        model = EquipmentVariant

        fields = [
            'size',
            'quantity'
        ]

        widgets = {
            'size': forms.TextInput(
                attrs={
                    'class': 'form-input'
                }
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-input',
                    'min': 1
                }
            )
        }