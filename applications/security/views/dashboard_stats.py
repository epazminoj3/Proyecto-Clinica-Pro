from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from datetime import date, timedelta, datetime
from decimal import Decimal

from applications.core.models import Paciente
from applications.doctor.models import CitaMedica, Atencion, Pago
from applications.security.models import User


@login_required
@require_http_methods(["GET"])
def dashboard_stats(request):
    """
    API para obtener estadísticas del dashboard en tiempo real
    """
    try:
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # === ESTADÍSTICAS DE USUARIOS ===
        total_usuarios = User.objects.filter(is_active=True).count()
        usuarios_mes_pasado = User.objects.filter(
            is_active=True,
            date_joined__date__lt=month_ago
        ).count()
        
        # Calcular porcentaje de crecimiento de usuarios
        if usuarios_mes_pasado > 0:
            crecimiento_usuarios = ((total_usuarios - usuarios_mes_pasado) / usuarios_mes_pasado) * 100
        else:
            crecimiento_usuarios = 100 if total_usuarios > 0 else 0
        
        # === ESTADÍSTICAS DE CITAS HOY ===
        citas_hoy = CitaMedica.objects.filter(fecha=today).count()
        citas_pendientes = CitaMedica.objects.filter(
            fecha=today,
            estado__in=['ocupado', 'disponible']
        ).count()
        
        # === ESTADÍSTICAS DE CONSULTAS ESTA SEMANA ===
        consultas_semana = Atencion.objects.filter(
            fecha_atencion__gte=week_ago,
            fecha_atencion__lte=today
        ).count()
        
        # === ESTADÍSTICAS DE INGRESOS ===
        # Ingresos del último mes
        ingresos_mes = Pago.objects.filter(
            fecha_pago__gte=month_ago,
            fecha_pago__lte=today,
            estado='pagado'
        ).aggregate(
            total=Count('monto')
        )
        
        # Calcular total de ingresos
        pagos_mes = Pago.objects.filter(
            fecha_pago__gte=month_ago,
            fecha_pago__lte=today,
            estado='pagado'
        )
        
        total_ingresos = sum(float(pago.monto) for pago in pagos_mes)
        
        # Ingresos del mes anterior para comparación
        two_months_ago = month_ago - timedelta(days=30)
        pagos_mes_anterior = Pago.objects.filter(
            fecha_pago__gte=two_months_ago,
            fecha_pago__lt=month_ago,
            estado='pagado'
        )
        
        ingresos_mes_anterior = sum(float(pago.monto) for pago in pagos_mes_anterior)
        
        # Calcular porcentaje de crecimiento de ingresos
        if ingresos_mes_anterior > 0:
            crecimiento_ingresos = ((total_ingresos - ingresos_mes_anterior) / ingresos_mes_anterior) * 100
        else:
            crecimiento_ingresos = 100 if total_ingresos > 0 else 0
        
        # === ESTADÍSTICAS ADICIONALES ===
        total_pacientes = Paciente.objects.filter(activo=True).count()
        citas_atendidas_hoy = CitaMedica.objects.filter(
            fecha=today,
            estado='atendido'
        ).count()
        
        # === PREPARAR RESPUESTA ===
        stats = {
            'usuarios': {
                'total': total_usuarios,
                'crecimiento': round(crecimiento_usuarios, 1),
                'icono': 'fas fa-users'
            },
            'citas_hoy': {
                'total': citas_hoy,
                'pendientes': citas_pendientes,
                'atendidas': citas_atendidas_hoy,
                'icono': 'fas fa-calendar-check'
            },
            'consultas': {
                'semana': consultas_semana,
                'periodo': 'Esta semana',
                'icono': 'fas fa-stethoscope'
            },
            'ingresos': {
                'total': round(total_ingresos, 2),
                'crecimiento': round(crecimiento_ingresos, 1),
                'moneda': '$',
                'periodo': 'Último mes',
                'icono': 'fas fa-dollar-sign'
            },
            'extras': {
                'total_pacientes': total_pacientes,
                'fecha_actualizacion': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
