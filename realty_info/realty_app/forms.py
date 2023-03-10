from django.forms import ModelForm,widgets,TextInput,Textarea,NumberInput
from . models import Flats
from dataclasses import fields


class FlatForm(ModelForm):
    class Meta:
        model=Flats
        fields=["city","district","rooms_number"]
        widgets={
            "city":TextInput(attrs={
                'class':'form-control',
                'placeholder':'Введите название населенного пункта'
            }),
            "district": TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите район'
            }),
            "rooms_number": NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите кол-во комнат'
            }),
        }