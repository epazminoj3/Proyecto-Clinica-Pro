from django import forms
from applications.core.models import Medicamento, TipoMedicamento, MarcaMedicamento


class MedicamentoForm(forms.ModelForm):
    """Formulario para crear y editar medicamentos"""
    
    class Meta:
        model = Medicamento
        fields = [
            'tipo', 'marca_medicamento', 'nombre', 'descripcion', 'concentracion',
            'via_administracion', 'cantidad', 'precio', 'comercial', 'foto', 'activo'
        ]
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'marca_medicamento': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Ibuprofeno, Paracetamol, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Uso, indicaciones, precauciones...'
            }),
            'concentracion': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': '500mg, 1g, 5%'
            }),
            'via_administracion': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 0
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': 0
            }),
            'comercial': forms.CheckboxInput(attrs={
                'class': 'mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }


class TipoMedicamentoForm(forms.ModelForm):
    """Formulario para crear y editar tipos de medicamento"""
    
    class Meta:
        model = TipoMedicamento
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Analgésico, Antibiótico, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción del tipo de medicamento...'
            }),
        }


class MarcaMedicamentoForm(forms.ModelForm):
    """Formulario para crear y editar marcas de medicamento"""
    
    class Meta:
        model = MarcaMedicamento
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Pfizer, Bayer, Novartis, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción de la marca...'
            }),
        }
