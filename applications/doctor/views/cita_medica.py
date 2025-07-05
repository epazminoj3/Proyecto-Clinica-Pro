from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q
from applications.doctor.models import CitaMedica
from applications.doctor.forms import CitaMedicaForm
from django.http import JsonResponse
from django.views import View
from datetime import datetime
from applications.security.components.mixin_crud import (
    PermissionMixin, ListViewMixin, CreateViewMixin, UpdateViewMixin, DeleteViewMixin
)


# ==================== VISTAS DE CITA MEDICA ====================
class CitaMedicaListView(PermissionMixin, ListViewMixin, ListView):
    model = CitaMedica
    template_name = 'doctor/cita_medica/list.html'
    context_object_name = 'citas'
    permission_required = 'doctor.view_citamedica'

    def get_queryset(self):
        # Búsqueda
        q1 = self.request.GET.get('q')
        
        if q1 is not None:
            self.query.add(Q(paciente__nombres__icontains=q1), Q.OR)
            self.query.add(Q(paciente__apellidos__icontains=q1), Q.OR)
            self.query.add(Q(paciente__cedula_ecuatoriana__icontains=q1), Q.OR)
            self.query.add(Q(paciente__dni__icontains=q1), Q.OR)
            self.query.add(Q(observaciones__icontains=q1), Q.OR)
        
        # Filtro por fecha
        fecha_filter = self.request.GET.get('fecha')
        if fecha_filter:
            self.query.add(Q(fecha=fecha_filter), Q.AND)
        
        # Filtro alfabético por nombre
        nombre_filter = self.request.GET.get('nombre_letra')
        if nombre_filter and nombre_filter != 'todos':
            self.query.add(Q(paciente__nombres__istartswith=nombre_filter), Q.AND)
        
        # Filtro alfabético por apellido
        apellido_filter = self.request.GET.get('apellido_letra')
        if apellido_filter and apellido_filter != 'todos':
            self.query.add(Q(paciente__apellidos__istartswith=apellido_filter), Q.AND)
        
        # Ordenamiento
        sort_by = self.request.GET.get('sort', 'fecha')
        direction = self.request.GET.get('direction', 'asc')
        
        if sort_by == 'paciente':
            # Ordenar por apellido primero, luego por nombre
            order_field = 'paciente__apellidos'
        elif sort_by == 'fecha':
            order_field = 'fecha'
        elif sort_by == 'hora':
            order_field = 'hora_cita'
        elif sort_by == 'estado':
            order_field = 'estado'
        else:
            order_field = 'fecha'
        
        if direction == 'desc':
            order_field = f'-{order_field}'
        
        # Aplicar query y ordenamiento
        queryset = (self.model.objects.filter(self.query)
                    .select_related('paciente')
                    .order_by(order_field, 'hora_cita'))
        
        # Si ordenamos por paciente, agregamos nombre como segundo criterio
        if sort_by == 'paciente':
            if direction == 'desc':
                return queryset.order_by(order_field, '-paciente__nombres', 'hora_cita')
            else:
                return queryset.order_by(order_field, 'paciente__nombres', 'hora_cita')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('doctor:cita_medica_create')
        context['search_query'] = self.request.GET.get('q', '')
        context['fecha_filter'] = self.request.GET.get('fecha', '')
        context['current_sort'] = self.request.GET.get('sort', 'fecha')
        context['current_direction'] = self.request.GET.get('direction', 'asc')
        context['nombre_filter'] = self.request.GET.get('nombre_letra', 'todos')
        context['apellido_filter'] = self.request.GET.get('apellido_letra', 'todos')
        
        # Letras del alfabeto para los filtros
        context['alfabeto'] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                               'N', 'Ñ', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        
        return context


class CitaMedicaCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = CitaMedica
    form_class = CitaMedicaForm
    template_name = 'doctor/cita_medica/form.html'
    permission_required = 'doctor.add_citamedica'
    
    def get_success_url(self):
        # Redirigir a la página de confirmación con el ID de la cita creada
        return reverse_lazy('doctor:cita_medica_confirmacion', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Crear Cita Médica'
        context['back_url'] = reverse_lazy('doctor:cita_medica_list')
        return context

    def get_initial(self):
        """Pre-llenar formulario con parámetros GET del chatbot"""
        initial = super().get_initial()
        
        # Obtener parámetros GET para pre-llenar el formulario
        field_mapping = {
            'fecha': 'fecha',
            'hora': 'hora_cita',
            'especialidad': 'especialidad',
            'observaciones': 'observaciones'
        }
        
        for param_name, field_name in field_mapping.items():
            value = self.request.GET.get(param_name)
            if value:
                initial[field_name] = value
        
        return initial

    def form_valid(self, form):
        """Manejar la creación de nuevo paciente si es necesario"""
        # Verificar si se está creando un nuevo paciente
        paciente_mode = self.request.POST.get('paciente_mode')
        
        if paciente_mode == 'new':
            # Crear nuevo paciente
            try:
                from applications.core.models import Paciente
                from applications.core.utils.paciente import SexoChoices, EstadoCivilChoices
                
                # Recopilar datos del nuevo paciente
                nuevo_paciente = Paciente.objects.create(
                    nombres=self.request.POST.get('nuevo_nombres'),
                    apellidos=self.request.POST.get('nuevo_apellidos'),
                    cedula_ecuatoriana=self.request.POST.get('nuevo_cedula'),
                    telefono=self.request.POST.get('nuevo_telefono'),
                    fecha_nacimiento=self.request.POST.get('nuevo_fecha_nacimiento'),
                    email=self.request.POST.get('nuevo_email') or None,
                    sexo=self.request.POST.get('nuevo_sexo'),
                    direccion=self.request.POST.get('nuevo_direccion'),
                    estado_civil=EstadoCivilChoices.SOLTERO,  # Valor por defecto
                    activo=True
                )
                
                # Asignar el nuevo paciente a la cita
                form.instance.paciente = nuevo_paciente
                
                # Agregar mensaje de éxito
                from django.contrib import messages
                messages.success(
                    self.request, 
                    f'Paciente {nuevo_paciente.nombre_completo} creado exitosamente y cita programada.'
                )
                
            except Exception as e:
                # Si hay error al crear paciente, mostrar mensaje de error
                from django.contrib import messages
                messages.error(
                    self.request, 
                    f'Error al crear el paciente: {str(e)}'
                )
                return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        """Personalizar el formulario para pasar datos POST"""
        form = super().get_form(form_class)
        # Pasar los datos POST al formulario para la validación condicional
        if self.request.method == 'POST':
            form.data = self.request.POST
        return form


class CitaMedicaUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = CitaMedica
    form_class = CitaMedicaForm
    template_name = 'doctor/cita_medica/form.html'
    success_url = reverse_lazy('doctor:cita_medica_list')
    permission_required = 'doctor.change_citamedica'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Cita Médica'
        context['back_url'] = self.success_url
        return context
    
    def get_initial(self):
        """Asegurar que los valores iniciales se carguen correctamente"""
        initial = super().get_initial()
        if self.object:
            if self.object.fecha:
                initial['fecha'] = self.object.fecha
            if self.object.hora_cita:
                initial['hora_cita'] = self.object.hora_cita
        return initial


class CitaMedicaDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = CitaMedica
    template_name = 'fragments/delete.html'
    success_url = reverse_lazy('doctor:cita_medica_list')
    permission_required = 'doctor.delete_citamedica'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Cita Médica'
        context['question'] = f'¿Está seguro de eliminar la cita de {self.object.paciente} el {self.object.fecha} a las {self.object.hora_cita}?'
        context['cancel_url'] = self.success_url
        return context
    
    def delete(self, request, *args, **kwargs):
        """Override delete method to add success message"""
        from django.contrib import messages
        cita = self.get_object()
        messages.success(request, f'La cita de {cita.paciente.nombre_completo} del {cita.fecha.strftime("%d/%m/%Y")} ha sido eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


class CitaMedicaDetailView(PermissionMixin, DetailView):
    model = CitaMedica
    template_name = 'doctor/cita_medica/detail.html'
    context_object_name = 'cita'
    permission_required = 'doctor.view_citamedica'


class VerificarDisponibilidadView(PermissionMixin, View):
    """Vista para verificar disponibilidad de citas vía AJAX"""
    permission_required = 'doctor.add_citamedica'
    
    def get(self, request):
        fecha_str = request.GET.get('fecha')
        hora_str = request.GET.get('hora')
        
        if not fecha_str or not hora_str:
            return JsonResponse({'disponible': True})
        
        try:
            # Convertir strings a objetos de fecha y hora
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
            
            # Buscar citas existentes en esa fecha y hora
            citas_existentes = CitaMedica.objects.filter(
                fecha=fecha,
                hora_cita=hora
            )
            
            if citas_existentes.exists():
                cita_existente = citas_existentes.first()
                return JsonResponse({
                    'disponible': False,
                    'mensaje': f'Ya existe una cita programada para el {fecha.strftime("%d/%m/%Y")} a las {hora.strftime("%H:%M")} con el paciente {cita_existente.paciente.nombre_completo}.'
                })
            else:
                return JsonResponse({'disponible': True})
                
        except ValueError:
            return JsonResponse({'disponible': True})


class CitaMedicaConfirmacionView(PermissionMixin, DetailView):
    """Vista de confirmación después de crear una cita"""
    model = CitaMedica
    template_name = 'doctor/cita_medica/confirmacion.html'
    context_object_name = 'cita'
    permission_required = 'doctor.view_citamedica'


class EnviarCorreoCitaView(PermissionMixin, View):
    """Vista para enviar correo de confirmación de cita"""
    permission_required = 'doctor.view_citamedica'
    
    def post(self, request, pk):
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        from smtplib import SMTPException
        
        try:
            cita = CitaMedica.objects.get(pk=pk)
            paciente = cita.paciente
            
            if not paciente.email:
                return JsonResponse({
                    'success': False, 
                    'message': 'El paciente no tiene correo electrónico registrado.'
                })
            
            # Renderizar el contenido del correo
            asunto = f'Confirmación de Cita Médica - {cita.fecha.strftime("%d/%m/%Y")}'
            mensaje = render_to_string('doctor/cita_medica/email_confirmacion.html', {
                'cita': cita,
                'paciente': paciente
            })
            
            # Enviar correo
            send_mail(
                asunto,
                '',  # Mensaje en texto plano (vacío porque usamos HTML)
                settings.DEFAULT_FROM_EMAIL,
                [paciente.email],
                html_message=mensaje,
                fail_silently=False
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'✅ Correo enviado exitosamente a {paciente.email}'
            })
            
        except CitaMedica.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Cita no encontrada.'
            })
        except SMTPException as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error SMTP: Verifique la configuración de correo. {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error al enviar correo: {str(e)}. Verifique la configuración en settings.py'
            })
