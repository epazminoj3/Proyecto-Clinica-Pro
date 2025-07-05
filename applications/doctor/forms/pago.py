from django import forms
from django.forms import inlineformset_factory
from applications.doctor.models import Pago, DetallePago


class PagoForm(forms.ModelForm):
    """Formulario para crear y editar pagos"""
    
    class Meta:
        model = Pago
        fields = [
            'atencion', 'metodo_pago', 'monto_total', 'estado', 'fecha_pago',
            'nombre_pagador', 'referencia_externa', 'evidencia_pago', 'observaciones', 'activo'
        ]
        widgets = {
            'atencion': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'required': True
            }),
            'metodo_pago': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'required': True
            }),
            'monto_total': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': 0,
                'required': True
            }),
            'estado': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'required': True
            }),
            'fecha_pago': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'datetime-local',
                'required': True
            }),
            'nombre_pagador': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Nombre de quien paga'
            }),
            'referencia_externa': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'ID de transacción PayPal, etc.'
            }),
            'evidencia_pago': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
                'accept': 'image/*,application/pdf,.doc,.docx'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos obligatorios
        self.fields['atencion'].required = True
        self.fields['metodo_pago'].required = True
        self.fields['monto_total'].required = True
        self.fields['estado'].required = True
        self.fields['fecha_pago'].required = True
        
        # Establecer valores por defecto
        if not self.instance.pk:
            self.fields['activo'].initial = True
            self.fields['estado'].initial = 'pendiente'


class DetallePagoForm(forms.ModelForm):
    """Formulario para crear y editar detalles de pago"""
    
    class Meta:
        model = DetallePago
        fields = [
            'pago', 'servicio_adicional', 'cantidad', 'precio_unitario', 
            'descuento_porcentaje', 'aplica_seguro', 'valor_seguro', 'descripcion_seguro'
        ]
        widgets = {
            'pago': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'required': True
            }),
            'servicio_adicional': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'required': True
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 1,
                'value': 1,
                'required': True
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 pl-8',
                'step': '0.01',
                'min': 0,
                'required': True,
                'placeholder': '0.00'
            }),
            'descuento_porcentaje': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 pr-8',
                'step': '0.01',
                'min': 0,
                'max': 100,
                'value': 0,
                'placeholder': '0'
            }),
            'aplica_seguro': forms.CheckboxInput(attrs={
                'class': 'mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
            'valor_seguro': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 pl-8',
                'step': '0.01',
                'min': 0,
                'placeholder': '0.00'
            }),
            'descripcion_seguro': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Ej: Saludsa Nivel 2, Ecuasanitas'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos obligatorios
        self.fields['servicio_adicional'].required = True
        self.fields['cantidad'].required = True
        self.fields['precio_unitario'].required = True
        
        # Establecer valores por defecto
        if not self.instance.pk:
            self.fields['cantidad'].initial = 1
            self.fields['descuento_porcentaje'].initial = 0
            self.fields['valor_seguro'].initial = 0
            self.fields['aplica_seguro'].initial = False


# Formset para manejar múltiples detalles de pago
DetallePagoFormSet = inlineformset_factory(
    Pago, DetallePago, 
    form=DetallePagoForm, 
    extra=1, 
    can_delete=True,
    min_num=0,
    validate_min=False
)
