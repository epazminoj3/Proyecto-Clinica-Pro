from django import forms
from applications.core.models import (
    Empleado, Cargo, Diagnostico, TipoGasto, GastoMensual, TipoSangre
)


class EmpleadoForm(forms.ModelForm):
    """Formulario para crear y editar empleados"""
    
    class Meta:
        model = Empleado
        fields = [
            'nombres', 'apellidos', 'cedula_ecuatoriana', 'dni', 'fecha_nacimiento',
            'cargo', 'sueldo', 'fecha_ingreso', 'direccion', 'latitud', 'longitud', 'foto', 'activo'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Ingrese los nombres'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Ingrese los apellidos'
            }),
            'cedula_ecuatoriana': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': '1234567890'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Documento internacional (opcional)'
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'date'
            }),
            'cargo': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'sueldo': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': 0
            }),
            'fecha_ingreso': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'date'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Dirección completa'
            }),
            'latitud': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': 'any'
            }),
            'longitud': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': 'any'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }


class CargoForm(forms.ModelForm):
    """Formulario para crear y editar cargos"""
    
    class Meta:
        model = Cargo
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Médico, Enfermero, Administrador, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción del cargo...'
            }),
        }


class DiagnosticoForm(forms.ModelForm):
    """Formulario para crear y editar diagnósticos"""
    
    class Meta:
        model = Diagnostico
        fields = ['codigo', 'descripcion', 'datos_adicionales']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'A09, J00, K35.2, etc.'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Descripción del diagnóstico'
            }),
            'datos_adicionales': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Observaciones clínicas adicionales...'
            }),
        }


class TipoGastoForm(forms.ModelForm):
    """Formulario para crear y editar tipos de gasto"""
    
    class Meta:
        model = TipoGasto
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Arriendo, Luz, Agua, Internet, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción del tipo de gasto...'
            }),
        }


class GastoMensualForm(forms.ModelForm):
    """Formulario para crear y editar gastos mensuales"""
    
    # Campos adicionales para información personal
    responsable = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Nombre del responsable del gasto (opcional)'
        }),
        help_text='Persona responsable de este gasto'
    )
    
    departamento = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Departamento o área (opcional)'
        }),
        help_text='Departamento o área donde se incurrió el gasto'
    )
    
    class Meta:
        model = GastoMensual
        fields = ['tipo_gasto', 'fecha', 'valor', 'observacion']
        widgets = {
            'tipo_gasto': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'date'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': 0
            }),
            'observacion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Comentario adicional (opcional)...'
            }),
        }


class TipoSangreForm(forms.ModelForm):
    """Formulario para crear y editar tipos de sangre"""
    
    class Meta:
        model = TipoSangre
        fields = ['tipo', 'descripcion']
        widgets = {
            'tipo': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'O+, A-, B+, AB-, etc.'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Descripción del tipo de sangre'
            }),
        }
