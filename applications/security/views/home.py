
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta
from applications.security.components.menu_module import MenuModule
from applications.security.components.mixin_crud import PermissionMixin
from applications.core.models import Paciente
from applications.doctor.models import CitaMedica, Atencion

class ModuloTemplateView(PermissionMixin,TemplateView):
    template_name = 'home.html'
   
    def get_context_data(self, **kwargs):
        #context = super().get_context_data(**kwargs)
        context={}
        context["title"]= "IC - Modulos"
        context["title1"]= "Modulos Disponibles"
        MenuModule(self.request).fill(context)
        
        # Agregar estadísticas reales
        context.update(self.get_statistics())
        
        print("estoy saliendo en el modulo template view")
       
        return context
    
    def get_statistics(self):
        """Obtener estadísticas reales del sistema"""
        today = date.today()
        
        # Estadísticas de pacientes
        total_pacientes = Paciente.objects.filter(activo=True).count()
        
        # Estadísticas de citas
        citas_hoy = CitaMedica.objects.filter(fecha=today).count()
        citas_pendientes = CitaMedica.objects.filter(
            fecha__gte=today,
            estado='pendiente'
        ).count()
        
        # Estadísticas de la semana
        inicio_semana = today - timedelta(days=today.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        citas_esta_semana = CitaMedica.objects.filter(
            fecha__range=[inicio_semana, fin_semana]
        ).count()
        
        # Estadísticas de atenciones
        atenciones_hoy = Atencion.objects.filter(
            fecha_atencion__date=today
        ).count()
        
        atenciones_esta_semana = Atencion.objects.filter(
            fecha_atencion__date__range=[inicio_semana, fin_semana]
        ).count()
        
        # Estadísticas del mes actual
        inicio_mes = today.replace(day=1)
        if today.month == 12:
            fin_mes = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fin_mes = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        citas_este_mes = CitaMedica.objects.filter(
            fecha__range=[inicio_mes, fin_mes]
        ).count()
        
        atenciones_este_mes = Atencion.objects.filter(
            fecha_atencion__date__range=[inicio_mes, fin_mes]
        ).count()
        
        # Ingresos estimados del mes (asumiendo un valor promedio por consulta)
        valor_promedio_consulta = 25.00  # Valor promedio por consulta
        ingresos_estimados = atenciones_este_mes * valor_promedio_consulta
        
        return {
            'stats': {
                'total_pacientes': total_pacientes,
                'citas_hoy': citas_hoy,
                'citas_pendientes': citas_pendientes,
                'citas_esta_semana': citas_esta_semana,
                'atenciones_hoy': atenciones_hoy,
                'atenciones_esta_semana': atenciones_esta_semana,
                'citas_este_mes': citas_este_mes,
                'atenciones_este_mes': atenciones_este_mes,
                'ingresos_estimados': ingresos_estimados,
            }
        }