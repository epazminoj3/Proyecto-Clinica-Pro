from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
import json
from applications.doctor.models import HorarioAtencion
from applications.doctor.forms import HorarioAtencionForm
from applications.doctor.utils.doctor import DiaSemanaChoices
from applications.security.components.mixin_crud import (
    PermissionMixin, ListViewMixin, CreateViewMixin, UpdateViewMixin, DeleteViewMixin
)


# ==================== VISTAS DE HORARIO DE ATENCION ====================
class HorarioAtencionListView(PermissionMixin, ListViewMixin, ListView):
    model = HorarioAtencion
    template_name = 'doctor/horario/list.html'
    context_object_name = 'horarios'
    permission_required = 'doctor.view_horarioatencion'

    def get_queryset(self):
        q1 = self.request.GET.get('q')
        
        if q1 is not None:
            self.query.add(Q(dia_semana__icontains=q1), Q.OR)
        
        return (self.model.objects.filter(self.query)
                .filter(activo=True)
                .order_by('dia_semana', 'hora_inicio'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('doctor:horario_create')
        return context


class HorarioAtencionCreateView(PermissionMixin, CreateViewMixin, CreateView):
    model = HorarioAtencion
    form_class = HorarioAtencionForm
    template_name = 'doctor/horario/form.html'
    success_url = reverse_lazy('doctor:horario_list')
    permission_required = 'doctor.add_horarioatencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Grabar Horario de Atención'
        context['back_url'] = self.success_url
        context['days_choices'] = DiaSemanaChoices.choices
        return context

    def form_valid(self, form):
        form.instance.activo = True
        return super().form_valid(form)


class HorarioAtencionUpdateView(PermissionMixin, UpdateViewMixin, UpdateView):
    model = HorarioAtencion
    form_class = HorarioAtencionForm
    template_name = 'doctor/horario/form.html'
    success_url = reverse_lazy('doctor:horario_list')
    permission_required = 'doctor.change_horarioatencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Actualizar Horario de Atención'
        context['back_url'] = self.success_url
        context['days_choices'] = DiaSemanaChoices.choices
        return context


class HorarioAtencionDeleteView(PermissionMixin, DeleteViewMixin, DeleteView):
    model = HorarioAtencion
    template_name = 'fragments/delete.html'
    success_url = reverse_lazy('doctor:horario_list')
    permission_required = 'doctor.delete_horarioatencion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Horario'
        context['question'] = f'¿Está seguro de eliminar el horario {self.object.dia_semana} {self.object.hora_inicio}-{self.object.hora_fin}?'
        context['cancel_url'] = self.success_url
        return context


# Vista de gestión dinámica de horarios
class HorarioGestionView(PermissionMixin, CreateViewMixin, CreateView):
    """Vista para gestionar todos los horarios de manera dinámica"""
    model = HorarioAtencion
    template_name = 'doctor/horario/form.html'
    success_url = reverse_lazy('doctor:horario_list')
    permission_required = 'doctor.add_horarioatencion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grabar'] = 'Gestionar Horarios'
        context['back_url'] = self.success_url
        context['days_choices'] = DiaSemanaChoices.choices
        return context
    
    def get_form_class(self):
        # No necesitamos formulario real, solo el template
        return HorarioAtencionForm


# ==================== VISTAS AJAX PARA HORARIOS ====================
class HorarioAjaxDayView(PermissionMixin, View):
    """Vista AJAX para obtener horario de un día específico"""
    permission_required = 'doctor.view_horarioatencion'
    
    def get(self, request, day_code):
        try:
            horario = HorarioAtencion.objects.filter(
                dia_semana=day_code, 
                activo=True
            ).first()
            
            if horario:
                schedule_data = {
                    'hora_inicio': horario.hora_inicio.strftime('%H:%M') if horario.hora_inicio else '',
                    'hora_fin': horario.hora_fin.strftime('%H:%M') if horario.hora_fin else '',
                    'intervalo_desde': horario.intervalo_desde.strftime('%H:%M') if horario.intervalo_desde else '',
                    'intervalo_hasta': horario.intervalo_hasta.strftime('%H:%M') if horario.intervalo_hasta else '',
                }
                return JsonResponse({
                    'success': True,
                    'schedule': schedule_data
                })
            else:
                return JsonResponse({
                    'success': False,
                    'schedule': None
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class HorarioAjaxSaveAllView(PermissionMixin, View):
    """Vista AJAX para guardar todos los horarios"""
    permission_required = 'doctor.add_horarioatencion'
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            schedules = data.get('schedules', {})
            
            saved_count = 0
            errors = []
            
            for day_code, schedule_data in schedules.items():
                try:
                    # Buscar horario existente
                    horario, created = HorarioAtencion.objects.get_or_create(
                        dia_semana=day_code,
                        defaults={
                            'activo': True
                        }
                    )
                    
                    # Verificar si se está enviando un horario vacío (para eliminar)
                    if not schedule_data.get('hora_inicio') and not schedule_data.get('hora_fin'):
                        if not created:  # Solo eliminar si ya existía
                            horario.delete()
                            saved_count += 1
                        continue
                    
                    # Actualizar datos solo si hay información válida
                    if schedule_data.get('hora_inicio'):
                        horario.hora_inicio = schedule_data['hora_inicio']
                    if schedule_data.get('hora_fin'):
                        horario.hora_fin = schedule_data['hora_fin']
                    
                    # Campos opcionales
                    horario.intervalo_desde = schedule_data.get('intervalo_desde') or None
                    horario.intervalo_hasta = schedule_data.get('intervalo_hasta') or None
                    
                    horario.activo = True
                    horario.save()
                    saved_count += 1
                    
                except Exception as e:
                    errors.append(f"Error en {day_code}: {str(e)}")
            
            if errors:
                return JsonResponse({
                    'success': False,
                    'error': '; '.join(errors),
                    'saved_count': saved_count
                })
            else:
                return JsonResponse({
                    'success': True,
                    'saved_count': saved_count,
                    'message': f'Se procesaron {saved_count} horarios correctamente'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
