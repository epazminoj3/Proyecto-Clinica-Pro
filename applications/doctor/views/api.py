from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
from applications.doctor.models import CitaMedica
from applications.security.components.mixin_crud import PermissionMixin


class CalendarDataAPI(PermissionMixin, View):
    """API para datos del calendario"""
    permission_required = 'doctor.view_citamedica'
    
    def get(self, request):
        try:
            # Obtener rango de fechas
            start_date = request.GET.get('start')
            end_date = request.GET.get('end')
            
            if not start_date or not end_date:
                return JsonResponse({'error': 'Fechas requeridas'}, status=400)
            
            # Obtener citas en el rango
            citas = CitaMedica.objects.filter(
                fecha__range=[start_date, end_date],
                activo=True
            ).select_related('paciente', 'doctor')
            
            # Formatear datos
            events = []
            for cita in citas:
                events.append({
                    'id': cita.id,
                    'date': cita.fecha.strftime('%Y-%m-%d'),
                    'time': cita.hora_cita.strftime('%H:%M'),
                    'patient_name': cita.paciente.nombres + ' ' + cita.paciente.apellidos,
                    'doctor_name': cita.doctor.nombres + ' ' + cita.doctor.apellidos,
                    'type': cita.tipo_cita or 'Consulta',
                    'status': cita.estado.lower() if cita.estado else 'programada'
                })
            
            return JsonResponse({
                'events': events,
                'success': True
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class TodayAppointmentsAPI(PermissionMixin, View):
    """API para citas de hoy"""
    permission_required = 'doctor.view_citamedica'
    
    def get(self, request):
        try:
            today = timezone.now().date()
            
            citas = CitaMedica.objects.filter(
                fecha=today,
                activo=True
            ).select_related('paciente', 'doctor').order_by('hora_cita')
            
            appointments = []
            for cita in citas:
                appointments.append({
                    'id': cita.id,
                    'time': cita.hora_cita.strftime('%H:%M'),
                    'patient_name': cita.paciente.nombres + ' ' + cita.paciente.apellidos,
                    'doctor_name': cita.doctor.nombres + ' ' + cita.doctor.apellidos,
                    'type': cita.tipo_cita or 'Consulta',
                    'status': cita.estado.lower() if cita.estado else 'programada'
                })
            
            return JsonResponse({
                'appointments': appointments,
                'success': True
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class UpcomingAppointmentsAPI(PermissionMixin, View):
    """API para próximas citas"""
    permission_required = 'doctor.view_citamedica'
    
    def get(self, request):
        try:
            today = timezone.now().date()
            next_week = today + timedelta(days=7)
            
            citas = CitaMedica.objects.filter(
                fecha__gt=today,
                fecha__lte=next_week,
                activo=True
            ).select_related('paciente', 'doctor').order_by('fecha', 'hora_cita')[:10]
            
            appointments = []
            for cita in citas:
                appointments.append({
                    'id': cita.id,
                    'date': cita.fecha.strftime('%d/%m'),
                    'time': cita.hora_cita.strftime('%H:%M'),
                    'patient_name': cita.paciente.nombres + ' ' + cita.paciente.apellidos,
                    'doctor_name': cita.doctor.nombres + ' ' + cita.doctor.apellidos,
                    'type': cita.tipo_cita or 'Consulta',
                    'status': cita.estado.lower() if cita.estado else 'programada'
                })
            
            return JsonResponse({
                'appointments': appointments,
                'success': True
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
