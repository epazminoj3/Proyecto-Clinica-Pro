from django import forms
from applications.doctor.models import ServiciosAdicionales


class ServiciosAdicionalesForm(forms.ModelForm):
    """Formulario para crear y editar servicios adicionales"""
    
    class Meta:
        model = ServiciosAdicionales
        fields = ['nombre_servicio', 'costo_servicio', 'descripcion']
        widgets = {
            'nombre_servicio': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Radiografía, Laboratorio, etc.'
            }),
            'costo_servicio': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': 0
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción del servicio adicional...'
            }),
        }
