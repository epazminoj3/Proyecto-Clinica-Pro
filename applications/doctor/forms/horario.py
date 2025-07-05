from django import forms
from applications.doctor.models import HorarioAtencion


class HorarioAtencionForm(forms.ModelForm):
    """Formulario para crear y editar horarios de atención"""
    
    class Meta:
        model = HorarioAtencion
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'intervalo_desde', 'intervalo_hasta']
        widgets = {
            'dia_semana': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'time'
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'time'
            }),
            'intervalo_desde': forms.TimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'time'
            }),
            'intervalo_hasta': forms.TimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'time'
            }),
        }
