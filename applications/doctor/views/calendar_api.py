from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import datetime, timedelta, time
import json
import calendar

from applications.doctor.models import CitaMedica, HorarioAtencion
from applications.doctor.utils.cita_medica import EstadoCitaChoices
from applications.security.models import GroupModulePermission
from applications.security.components.mixin_crud import PermissionMixin


class CalendarDataView(PermissionMixin, View):
    """
    API para obtener datos del calendario de citas médicas
    """
    permission_required = 'doctor.view_citamedica'
    
    def get(self, request, *args, **kwargs):
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        
        # Obtener el primer y último día del mes
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Obtener citas del mes
        citas = CitaMedica.objects.filter(
            fecha__range=[first_day, last_day]
        ).select_related('paciente').order_by('fecha', 'hora_cita')
        
        # Organizar citas por día
        citas_por_dia = {}
        for cita in citas:
            dia = cita.fecha.day
            if dia not in citas_por_dia:
                citas_por_dia[dia] = []
            
            citas_por_dia[dia].append({
                'id': cita.id,
                'hora': cita.hora_cita.strftime('%H:%M'),
                'paciente': cita.paciente.nombre_completo,
                'estado': cita.estado,
                'observaciones': cita.observaciones or ''
            })
        
        # Obtener horarios de atención disponibles
        horarios = self.get_horarios_disponibles()
        
        # Información del calendario
        # Configurar el calendario para que comience en domingo (6)
        cal_obj = calendar.Calendar(firstweekday=6)
        cal = cal_obj.monthdayscalendar(year, month)
        
        return JsonResponse({
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar_matrix': cal,
            'citas_por_dia': citas_por_dia,
            'horarios_disponibles': horarios,
            'estados_cita': dict(EstadoCitaChoices.choices)
        })
    
    def get_horarios_disponibles(self):
        """Obtener horarios de atención disponibles"""
        horarios = HorarioAtencion.objects.filter(activo=True)
        horarios_data = []
        
        for horario in horarios:
            # Generar slots de 1 hora
            slots = []
            hora_actual = horario.hora_inicio
            hora_fin = horario.hora_fin
            
            # Intervalos de 1 hora
            while hora_actual < hora_fin:
                # Verificar si estamos en el intervalo de pausa
                if (horario.intervalo_desde and horario.intervalo_hasta and 
                    horario.intervalo_desde <= hora_actual < horario.intervalo_hasta):
                    # Saltar al final del intervalo de pausa
                    hora_actual = horario.intervalo_hasta
                    if hora_actual >= hora_fin:
                        break
                    continue
                
                # Agregar el slot actual
                slot_time = hora_actual.strftime('%H:%M')
                slots.append(slot_time)
                
                # Sumar 1 hora
                hora_datetime = datetime.combine(datetime.today(), hora_actual)
                hora_datetime += timedelta(hours=1)
                hora_actual = hora_datetime.time()
            
            horarios_data.append({
                'dia_semana': horario.dia_semana,
                'slots': slots
            })
        
        return horarios_data


@method_decorator(csrf_exempt, name='dispatch')
class CalendarAvailabilityView(PermissionMixin, View):
    """
    API para verificar disponibilidad de horarios específicos
    """
    permission_required = 'doctor.add_citamedica'
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            fecha_str = data.get('fecha')
            hora_str = data.get('hora')
            
            # Validar datos
            if not fecha_str or not hora_str:
                return JsonResponse({'error': 'Fecha y hora son requeridas'}, status=400)
            
            # Convertir strings a objetos datetime
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
            
            # Verificar si ya existe una cita en ese horario
            cita_existente = CitaMedica.objects.filter(
                fecha=fecha,
                hora_cita=hora
            ).exists()
            
            if cita_existente:
                return JsonResponse({
                    'disponible': False,
                    'mensaje': 'Ya existe una cita programada en este horario'
                })
            
            # Verificar que esté dentro de los horarios de atención
            dia_semana = fecha.strftime('%A').lower()
            dias_mapping = {
                'monday': 'lunes',
                'tuesday': 'martes', 
                'wednesday': 'miercoles',
                'thursday': 'jueves',
                'friday': 'viernes',
                'saturday': 'sabado',
                'sunday': 'domingo'
            }
            dia_semana_es = dias_mapping.get(dia_semana, '')
            
            horario = HorarioAtencion.objects.filter(
                dia_semana=dia_semana_es,
                activo=True
            ).first()
            
            if not horario:
                return JsonResponse({
                    'disponible': False,
                    'mensaje': 'No hay horarios de atención configurados para este día'
                })
            
            # Verificar que esté dentro del rango de atención
            if not (horario.hora_inicio <= hora <= horario.hora_fin):
                return JsonResponse({
                    'disponible': False,
                    'mensaje': f'Horario fuera del rango de atención ({horario.hora_inicio} - {horario.hora_fin})'
                })
            
            # Verificar que no esté en el intervalo de pausa
            if (horario.intervalo_desde and horario.intervalo_hasta and 
                horario.intervalo_desde <= hora < horario.intervalo_hasta):
                return JsonResponse({
                    'disponible': False,
                    'mensaje': f'Horario en pausa ({horario.intervalo_desde} - {horario.intervalo_hasta})'
                })
            
            return JsonResponse({
                'disponible': True,
                'mensaje': 'Horario disponible',
                'url_crear_cita': f'/doctor/cita_medica/crear/?fecha={fecha_str}&hora={hora_str}'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': f'Error en formato de fecha/hora: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UpdateAppointmentStatusView(PermissionMixin, View):
    """
    API para actualizar el estado de citas pasadas automáticamente
    """
    permission_required = 'doctor.change_citamedica'
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            appointments = data.get('appointments', [])
            
            if not appointments:
                return JsonResponse({'error': 'No se enviaron citas para actualizar'}, status=400)
            
            updated_count = 0
            errors = []
            
            for appointment in appointments:
                try:
                    appointment_id = appointment.get('id')
                    if not appointment_id:
                        errors.append(f'ID de cita faltante para {appointment.get("paciente", "paciente desconocido")}')
                        continue
                    
                    # Buscar la cita y verificar que efectivamente esté pasada
                    cita = CitaMedica.objects.get(id=appointment_id)
                    today = datetime.now().date()
                    
                    # Solo actualizar si la cita está realmente pasada y no está completada
                    if cita.fecha < today and cita.estado not in [EstadoCitaChoices.NO_ASISTIO, EstadoCitaChoices.COMPLETADA, EstadoCitaChoices.ATENDIDO]:
                        cita.estado = EstadoCitaChoices.NO_ASISTIO
                        cita.save()
                        updated_count += 1
                    
                except CitaMedica.DoesNotExist:
                    errors.append(f'Cita con ID {appointment_id} no encontrada')
                except Exception as e:
                    errors.append(f'Error al actualizar cita {appointment_id}: {str(e)}')
            
            response_data = {
                'success': True,
                'updated_count': updated_count,
                'message': f'Se actualizaron {updated_count} citas como "No asistió"'
            }
            
            if errors:
                response_data['errors'] = errors
                response_data['message'] += f' ({len(errors)} errores)'
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MarcarCitaAtendidaView(PermissionMixin, View):
    """
    API para marcar una cita como atendida
    """
    permission_required = 'doctor.change_citamedica'
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            cita_id = data.get('cita_id')
            
            if not cita_id:
                return JsonResponse({'error': 'ID de cita es requerido'}, status=400)
            
            try:
                cita = CitaMedica.objects.get(id=cita_id)
                
                # Verificar que la cita esté en un estado que permita ser marcada como atendida
                if cita.estado in [EstadoCitaChoices.ATENDIDO, EstadoCitaChoices.COMPLETADA]:
                    return JsonResponse({
                        'success': False,
                        'message': f'La cita ya está marcada como {cita.get_estado_display()}'
                    })
                
                # Marcar como atendida
                cita.estado = EstadoCitaChoices.ATENDIDO
                cita.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Cita marcada como atendida exitosamente',
                    'nuevo_estado': cita.get_estado_display()
                })
                
            except CitaMedica.DoesNotExist:
                return JsonResponse({'error': 'Cita no encontrada'}, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
