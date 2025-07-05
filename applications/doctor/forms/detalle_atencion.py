from django import forms
from applications.doctor.models import DetalleAtencion


class DetalleAtencionForm(forms.ModelForm):
    """Formulario para crear y editar detalles de atención (medicamentos)"""
    
    class Meta:
        model = DetalleAtencion
        fields = ['atencion', 'medicamento', 'cantidad', 'prescripcion', 'duracion_tratamiento', 'frecuencia_diaria']
        widgets = {
            'atencion': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'medicamento': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 1
            }),
            'prescripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Tomar 1 tableta cada 8 horas con alimentos...'
            }),
            'duracion_tratamiento': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 1
            }),
            'frecuencia_diaria': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 1,
                'max': 24
            }),
        }
