from django import forms
from django.core.exceptions import ValidationError
from applications.doctor.models import CitaMedica
from datetime import datetime


class CitaMedicaForm(forms.ModelForm):
    """Formulario para crear y editar citas médicas"""
    
    # Campos adicionales para nuevo paciente
    nuevo_nombres = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ej: María José'
        })
    )
    
    nuevo_apellidos = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ej: García López'
        })
    )
    
    nuevo_cedula = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '1234567890',
            'maxlength': '10'
        })
    )
    
    nuevo_telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ej: 0998765432'
        })
    )
    
    nuevo_fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'date'
        })
    )
    
    nuevo_email = forms.EmailField(
        max_length=100,
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'ejemplo@correo.com'
        })
    )
    
    nuevo_sexo = forms.ChoiceField(
        choices=[
            ('', 'Seleccionar...'),
            ('masculino', 'Masculino'),
            ('femenino', 'Femenino')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    nuevo_direccion = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ej: Av. Principal 123, Quito'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que el campo paciente no sea requerido por defecto
        self.fields['paciente'].required = False
        
        # Asegurar que los valores se carguen correctamente para edición
        if self.instance and self.instance.pk:
            try:
                # Debug: imprimir valores actuales
                print(f"Debug - Fecha actual: {self.instance.fecha}")
                print(f"Debug - Hora actual: {self.instance.hora_cita}")
                
                # Establecer valores iniciales directamente en los widgets
                if self.instance.fecha:
                    self.fields['fecha'].widget.attrs['value'] = self.instance.fecha.strftime('%Y-%m-%d')
                    
                if self.instance.hora_cita:
                    self.fields['hora_cita'].widget.attrs['value'] = self.instance.hora_cita.strftime('%H:%M')
                    
            except Exception as e:
                print(f"Error al cargar valores iniciales: {e}")
    
    def clean_paciente(self):
        """Validación condicional del campo paciente"""
        paciente_mode = self.data.get('paciente_mode') if hasattr(self, 'data') else None
        
        # Si el formulario incluye el campo paciente_mode y está en modo 'new', 
        # no requerir el campo paciente
        if paciente_mode == 'new':
            return None
        
        # En cualquier otro caso, validar normalmente
        paciente = self.cleaned_data.get('paciente')
        if not paciente:
            raise ValidationError('Este campo es obligatorio.')
        return paciente
    
    def clean(self):
        """Validación personalizada para evitar citas duplicadas en la misma fecha y hora"""
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_cita = cleaned_data.get('hora_cita')
        
        # Validar datos del nuevo paciente si está en modo 'new'
        paciente_mode = self.data.get('paciente_mode') if hasattr(self, 'data') else None
        
        if paciente_mode == 'new':
            # Validar campos obligatorios del nuevo paciente
            campos_requeridos = {
                'nuevo_nombres': 'Nombres',
                'nuevo_apellidos': 'Apellidos',
                'nuevo_cedula': 'Cédula',
                'nuevo_telefono': 'Teléfono',
                'nuevo_fecha_nacimiento': 'Fecha de nacimiento',
                'nuevo_sexo': 'Sexo',
                'nuevo_direccion': 'Dirección'
            }
            
            errores = {}
            for campo, nombre in campos_requeridos.items():
                valor = cleaned_data.get(campo) or self.data.get(campo)
                if not valor:
                    errores[campo] = f'{nombre} es obligatorio.'
            
            # Validar cédula ecuatoriana
            cedula = cleaned_data.get('nuevo_cedula') or self.data.get('nuevo_cedula')
            if cedula:
                if not self.validar_cedula_ecuatoriana(cedula):
                    errores['nuevo_cedula'] = 'La cédula ecuatoriana no es válida.'
                
                # Verificar si ya existe un paciente con esa cédula
                from applications.core.models import Paciente
                if Paciente.objects.filter(cedula_ecuatoriana=cedula).exists():
                    errores['nuevo_cedula'] = 'Ya existe un paciente con esta cédula.'
            
            if errores:
                raise ValidationError(errores)
        
        if fecha and hora_cita:
            # Crear queryset para buscar citas existentes
            citas_existentes = CitaMedica.objects.filter(
                fecha=fecha,
                hora_cita=hora_cita
            )
            
            # Si estamos editando, excluir la cita actual de la búsqueda
            if self.instance and self.instance.pk:
                citas_existentes = citas_existentes.exclude(pk=self.instance.pk)
            
            # Si encontramos alguna cita, lanzar error de validación
            if citas_existentes.exists():
                cita_existente = citas_existentes.first()
                raise ValidationError({
                    'fecha': f'Ya existe una cita programada para el {fecha.strftime("%d/%m/%Y")} a las {hora_cita.strftime("%H:%M")} con el paciente {cita_existente.paciente.nombre_completo}.',
                    'hora_cita': 'Esta hora ya está ocupada en la fecha seleccionada.'
                })
        
        return cleaned_data
    
    def validar_cedula_ecuatoriana(self, cedula):
        """Validar cédula ecuatoriana usando el algoritmo oficial"""
        if not cedula or len(cedula) != 10:
            return False
        
        # Verificar que todos los caracteres sean dígitos
        if not cedula.isdigit():
            return False
        
        # Convertir a lista de enteros
        try:
            digitos = [int(d) for d in cedula]
        except ValueError:
            return False
        
        # Los primeros dos dígitos deben ser entre 01 y 24 (provincias)
        provincia = digitos[0] * 10 + digitos[1]
        if provincia < 1 or provincia > 24:
            return False
        
        # El tercer dígito debe ser menor a 6 (para cédulas de personas naturales)
        if digitos[2] > 5:
            return False
        
        # Algoritmo de validación
        suma = 0
        coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        
        for i in range(9):
            producto = digitos[i] * coeficientes[i]
            if producto > 9:
                producto -= 9
            suma += producto
        
        # Calcular dígito verificador
        residuo = suma % 10
        digito_verificador = (10 - residuo) % 10
        
        return digito_verificador == digitos[9]

    class Meta:
        model = CitaMedica
        fields = ['paciente', 'fecha', 'hora_cita', 'estado', 'observaciones']
        widgets = {
            'paciente': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'date'
            }),
            'hora_cita': forms.TimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'time'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
        }
    
    class Meta:
        model = CitaMedica
        fields = ['paciente', 'fecha', 'hora_cita', 'estado', 'observaciones']
        widgets = {
            'paciente': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'date'
            }),
            'hora_cita': forms.TimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'time'
            }),
            'estado': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
        }
