# -*- coding: utf-8 -*-
"""
Herramientas de consulta a base de datos para el chatbot IA
Permite al chatbot acceder a información de la base de datos
"""

import json
import logging
from datetime import datetime, timedelta
from django.db.models import Count, Q, Sum
from django.utils import timezone

# Importar modelos
from applications.core.models import (
    Paciente, Doctor, Empleado, Medicamento, Diagnostico,
    TipoSangre, Especialidad, Cargo, TipoMedicamento, MarcaMedicamento,
    TipoGasto, GastoMensual
)
from applications.doctor.models import (
    CitaMedica, Atencion, DetalleAtencion, Pago, DetallePago,
    HorarioAtencion, ServiciosAdicionales
)

logger = logging.getLogger(__name__)

class DatabaseTools:
    """Herramientas para consultar la base de datos desde el chatbot"""
    
    def __init__(self):
        self.herramientas_disponibles = {
            'contar_citas': self.contar_citas,
            'contar_pacientes': self.contar_pacientes,
            'contar_doctores': self.contar_doctores,
            'listar_especialidades': self.listar_especialidades,
            'citas_hoy': self.citas_hoy,
            'citas_proximas': self.citas_proximas,
            'citas_por_fecha': self.citas_por_fecha,
            'pacientes_recientes': self.pacientes_recientes,
            'ingresos_mes': self.ingresos_mes,
            'medicamentos_frecuentes': self.medicamentos_frecuentes,
            'diagnosticos_frecuentes': self.diagnosticos_frecuentes,
            'buscar_paciente': self.buscar_paciente,
            'buscar_doctor': self.buscar_doctor,
            'estadisticas_generales': self.estadisticas_generales,
        }
    
    def ejecutar_herramienta(self, nombre_herramienta, parametros=None):
        """Ejecuta una herramienta específica"""
        try:
            if nombre_herramienta not in self.herramientas_disponibles:
                return {"error": f"Herramienta '{nombre_herramienta}' no disponible"}
            
            if parametros:
                return self.herramientas_disponibles[nombre_herramienta](**parametros)
            else:
                return self.herramientas_disponibles[nombre_herramienta]()
                
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {nombre_herramienta}: {e}")
            return {"error": str(e)}
    
    def contar_citas(self, estado=None, fecha_desde=None, fecha_hasta=None):
        """Cuenta las citas médicas con filtros opcionales"""
        try:
            queryset = CitaMedica.objects.all()
            
            if estado:
                queryset = queryset.filter(estado=estado)
            
            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)
            
            # Desglose por estado
            desglose_estados = CitaMedica.objects.values('estado').annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')
            
            return {
                "total_citas": queryset.count(),
                "desglose_estados": list(desglose_estados),
                "consulta": "conteo de citas médicas"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def contar_pacientes(self, activos_solo=False):
        """Cuenta los pacientes registrados"""
        try:
            total = Paciente.objects.count()
            activos = Paciente.objects.filter(activo=True).count()
            inactivos = total - activos
            
            if activos_solo:
                return {
                    "total_pacientes": activos,
                    "consulta": "pacientes activos"
                }
            
            return {
                "total_pacientes": total,
                "activos": activos,
                "inactivos": inactivos,
                "consulta": "conteo de pacientes"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def contar_doctores(self, activos_solo=False):
        """Cuenta los doctores registrados"""
        try:
            total = Doctor.objects.count()
            activos = Doctor.objects.filter(activo=True).count()
            inactivos = total - activos
            
            # Desglose por especialidad
            especialidades = Doctor.objects.values('especialidad__nombre').annotate(
                cantidad=Count('id')
            ).order_by('-cantidad')
            
            resultado = {
                "total_doctores": total,
                "especialidades": list(especialidades),
                "consulta": "conteo de doctores"
            }
            
            if not activos_solo:
                resultado.update({
                    "activos": activos,
                    "inactivos": inactivos
                })
            
            return resultado
            
        except Exception as e:
            return {"error": str(e)}
    
    def listar_especialidades(self):
        """Lista todas las especialidades médicas"""
        try:
            especialidades = Especialidad.objects.annotate(
                num_doctores=Count('especialidades')
            ).values('nombre', 'num_doctores').order_by('nombre')
            
            return {
                "especialidades": list(especialidades),
                "total_especialidades": especialidades.count(),
                "consulta": "especialidades médicas"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def citas_hoy(self):
        """Obtiene las citas de hoy"""
        try:
            hoy = timezone.now().date()
            citas = CitaMedica.objects.filter(
                fecha=hoy
            ).select_related(
                'paciente'
            ).values(
                'hora_cita',
                'paciente__nombres',
                'paciente__apellidos', 
                'estado',
                'observaciones'
            ).order_by('hora_cita')
            
            return {
                "fecha": hoy.strftime("%Y-%m-%d"),
                "total_citas_hoy": citas.count(),
                "citas": list(citas),
                "consulta": "citas de hoy"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def citas_proximas(self, dias=7):
        """Obtiene las citas de los próximos días"""
        try:
            fecha_inicio = timezone.now().date()
            fecha_fin = fecha_inicio + timedelta(days=dias)
            
            citas = CitaMedica.objects.filter(
                fecha__range=[fecha_inicio, fecha_fin]
            ).select_related(
                'paciente'
            ).values(
                'fecha',
                'hora_cita',
                'paciente__nombres',
                'paciente__apellidos',
                'estado'
            ).order_by('fecha', 'hora_cita')
            
            return {
                "periodo": f"{fecha_inicio} a {fecha_fin}",
                "total_citas": citas.count(),
                "citas": list(citas),
                "consulta": f"citas próximos {dias} días"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def citas_por_fecha(self, fecha=None):
        """Obtiene las citas de una fecha específica"""
        try:
            from datetime import datetime
            
            # Si no se pasa fecha, usar hoy
            if not fecha:
                fecha = timezone.now().date()
            
            # Convertir string a fecha
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
                except ValueError:
                    # Intentar otros formatos
                    try:
                        fecha = datetime.strptime(fecha, "%d/%m/%Y").date()
                    except ValueError:
                        return {"error": f"Formato de fecha inválido: {fecha}"}
            
            citas = CitaMedica.objects.filter(
                fecha=fecha
            ).select_related(
                'paciente'
            ).values(
                'hora_cita',
                'paciente__nombres',
                'paciente__apellidos',
                'estado',
                'observaciones'
            ).order_by('hora_cita')
            
            return {
                "fecha": fecha.strftime("%Y-%m-%d"),
                "fecha_mostrar": fecha.strftime("%d/%m/%Y"),
                "total_citas_fecha": citas.count(),
                "citas": list(citas),
                "consulta": f"citas del {fecha.strftime('%d/%m/%Y')}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def pacientes_recientes(self, dias=30):
        """Obtiene pacientes registrados recientemente"""
        try:
            fecha_limite = timezone.now() - timedelta(days=dias)
            
            # Usar campo 'id' como aproximación a fecha de creación si no existe fecha_creacion
            pacientes = Paciente.objects.filter(
                id__gte=Paciente.objects.filter().order_by('id').first().id if Paciente.objects.exists() else 0
            ).values(
                'nombres',
                'apellidos',
                'cedula_ecuatoriana',
                'tipo_sangre__tipo'
            ).order_by('-id')[:dias]  # Tomar los últimos registros por ID
            
            return {
                "periodo_dias": dias,
                "total_pacientes_nuevos": pacientes.count(),
                "pacientes": list(pacientes),
                "consulta": f"pacientes últimos {dias} días"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def ingresos_mes(self, mes=None, año=None):
        """Calcula ingresos del mes"""
        try:
            if not mes:
                mes = timezone.now().month
            if not año:
                año = timezone.now().year
            
            pagos = Pago.objects.filter(
                fecha_pago__month=mes,
                fecha_pago__year=año
            )
            
            total_ingresos = pagos.aggregate(
                total=Sum('total_pagar')
            )['total'] or 0
            
            # Desglose por tipo de pago
            tipos_pago = pagos.values('tipo_pago').annotate(
                cantidad=Count('id'),
                monto=Sum('total_pagar')
            ).order_by('-monto')
            
            return {
                "mes": mes,
                "año": año,
                "total_ingresos": float(total_ingresos),
                "numero_pagos": pagos.count(),
                "tipos_pago": list(tipos_pago),
                "consulta": f"ingresos {mes}/{año}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def medicamentos_frecuentes(self, limite=10):
        """Obtiene medicamentos más recetados"""
        try:
            # Usar el campo correcto para marca
            medicamentos = DetalleAtencion.objects.values(
                'medicamento__nombre',
                'medicamento__marca_medicamento__nombre'
            ).annotate(
                veces_recetado=Count('id')
            ).order_by('-veces_recetado')[:limite]
            
            return {
                "medicamentos_frecuentes": list(medicamentos),
                "limite": limite,
                "consulta": f"top {limite} medicamentos más recetados"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def diagnosticos_frecuentes(self, limite=10):
        """Obtiene diagnósticos más comunes"""
        try:
            diagnosticos = Atencion.objects.values(
                'diagnostico__nombre'
            ).annotate(
                frecuencia=Count('id')
            ).order_by('-frecuencia')[:limite]
            
            return {
                "diagnosticos_frecuentes": list(diagnosticos),
                "limite": limite,
                "consulta": f"top {limite} diagnósticos más frecuentes"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def buscar_paciente(self, criterio):
        """Busca pacientes por nombre o cédula"""
        try:
            pacientes = Paciente.objects.filter(
                Q(nombres__icontains=criterio) |
                Q(apellidos__icontains=criterio) |
                Q(cedula_ecuatoriana__icontains=criterio)
            ).values(
                'nombres',
                'apellidos', 
                'cedula_ecuatoriana',
                'telefono',
                'tipo_sangre__tipo',
                'activo'
            )[:10]
            
            return {
                "criterio_busqueda": criterio,
                "pacientes_encontrados": list(pacientes),
                "total": pacientes.count(),
                "consulta": f"búsqueda paciente: {criterio}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def buscar_doctor(self, criterio):
        """Busca doctores por nombre o especialidad"""
        try:
            doctores = Doctor.objects.filter(
                Q(nombres__icontains=criterio) |
                Q(apellidos__icontains=criterio) |
                Q(especialidad__nombre__icontains=criterio)
            ).select_related('especialidad').values(
                'nombres',
                'apellidos',
                'ruc', 
                'especialidad__nombre',
                'telefonos',
                'activo'
            )[:10]
            
            return {
                "criterio_busqueda": criterio,
                "doctores_encontrados": list(doctores),
                "total": doctores.count(),
                "consulta": f"búsqueda doctor: {criterio}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def estadisticas_generales(self):
        """Obtiene estadísticas generales del sistema"""
        try:
            stats = {
                "pacientes": {
                    "total": Paciente.objects.count(),
                    "activos": Paciente.objects.filter(activo=True).count()
                },
                "doctores": {
                    "total": Doctor.objects.count(),
                    "activos": Doctor.objects.filter(activo=True).count()
                },
                "citas": {
                    "total": CitaMedica.objects.count(),
                    "hoy": CitaMedica.objects.filter(fecha=timezone.now().date()).count(),
                    "pendientes": CitaMedica.objects.filter(estado='Programada').count()
                },
                "atenciones": {
                    "total": Atencion.objects.count(),
                    "este_mes": Atencion.objects.filter(
                        fecha_atencion__month=timezone.now().month,
                        fecha_atencion__year=timezone.now().year
                    ).count()
                },
                "medicamentos": Medicamento.objects.filter(activo=True).count(),
                "especialidades": Especialidad.objects.count(),
                "consulta": "estadísticas generales del sistema"
            }
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}

    def formatear_respuesta_bd(self, datos, titulo):
        """Formatea respuesta de consulta a base de datos con espaciado mejorado"""
        if "error" in datos:
            return {
                "accion": "consulta_bd_error",
                "datos": {},
                "respuesta": f"❌ Error: {datos['error']}",
                "confianza": 0.0,
                "necesita_aclaracion": False,
                "campos_faltantes": [],
                "formulario_url": None
            }
        
        # Formatear respuesta legible
        respuesta = f"📊 **{titulo}**\n\n"
        formulario_url = None  # URL de redirección apropiada
        
        # Estadísticas generales
        if 'total_citas' in datos:
            respuesta += f"📅 **Total de citas:** {datos['total_citas']}\n"
            formulario_url = "/doctor/cita_medica/"  # Ver todas las citas
            if 'desglose_estados' in datos and datos['desglose_estados']:
                respuesta += "📋 **Por estado:**\n"
                for estado in datos['desglose_estados']:
                    respuesta += f"   • {estado['estado']}: {estado['cantidad']}\n"
        
        elif 'total_pacientes' in datos:
            respuesta += f"👥 **Total de pacientes:** {datos['total_pacientes']}\n"
            respuesta += f"✅ **Activos:** {datos.get('activos', 'N/A')}\n"
            respuesta += f"❌ **Inactivos:** {datos.get('inactivos', 'N/A')}\n"
            formulario_url = "/core/pacientes/"  # Ver todos los pacientes
        
        elif 'total_doctores' in datos:
            respuesta += f"👨‍⚕️ **Total de doctores:** {datos['total_doctores']}\n"
            formulario_url = "/core/doctores/"  # Ver todos los doctores
            if 'especialidades' in datos and datos['especialidades']:
                respuesta += "🏥 **Por especialidad:**\n"
                for esp in datos['especialidades']:
                    respuesta += f"   • {esp['especialidad__nombre']}: {esp['cantidad']}\n"
        
        elif 'total_citas_hoy' in datos:
            if datos['total_citas_hoy'] == 0:
                respuesta += f"📅 **No hay ninguna cita programada para hoy ({datos.get('fecha', '')})**\n"
                respuesta += "🔍 **Puedes revisar la agenda completa usando el botón de abajo**\n"
            else:
                respuesta += f"📅 **Citas para hoy ({datos.get('fecha', '')}):** {datos['total_citas_hoy']}\n"
            
            # URL con filtro de fecha para hoy
            formulario_url = f"/doctor/cita_medica/?fecha={datos.get('fecha', '')}"
            if datos['total_citas_hoy'] > 0 and 'citas' in datos:
                respuesta += "\n📋 **Citas del día:**\n\n"
                for i, cita in enumerate(datos['citas'][:5], 1):  # Mostrar máximo 5
                    respuesta += f"**Cita {i}:**\n"
                    respuesta += f"🕐 Hora: {cita['hora_cita']}\n"
                    respuesta += f"👤 Paciente: {cita['paciente__nombres']} {cita['paciente__apellidos']}\n"
                    respuesta += f"📊 Estado: {cita['estado']}\n"
                    if cita.get('observaciones'):
                        respuesta += f"📝 Observaciones: {cita['observaciones']}\n"
                    respuesta += "\n"
                if len(datos['citas']) > 5:
                    respuesta += f"📌 *... y {len(datos['citas']) - 5} citas más (ver listado completo)*\n"
        
        elif 'total_citas_fecha' in datos:
            if datos['total_citas_fecha'] == 0:
                respuesta += f"📅 **No hay ninguna cita programada para el {datos.get('fecha_mostrar', '')}**\n"
                respuesta += "🔍 **Puedes revisar la agenda completa usando el botón de abajo**\n"
            else:
                respuesta += f"📅 **Citas para el {datos.get('fecha_mostrar', '')}:** {datos['total_citas_fecha']}\n"
            
            # URL con filtro de fecha específica
            formulario_url = f"/doctor/cita_medica/?fecha={datos.get('fecha', '')}"
            if datos['total_citas_fecha'] > 0 and 'citas' in datos:
                respuesta += "\n📋 **Citas del día:**\n\n"
                for i, cita in enumerate(datos['citas'][:5], 1):  # Mostrar máximo 5
                    respuesta += f"**Cita {i}:**\n"
                    respuesta += f"🕐 Hora: {cita['hora_cita']}\n"
                    respuesta += f"👤 Paciente: {cita['paciente__nombres']} {cita['paciente__apellidos']}\n"
                    respuesta += f"📊 Estado: {cita['estado']}\n"
                    if cita.get('observaciones'):
                        respuesta += f"📝 Observaciones: {cita['observaciones']}\n"
                    respuesta += "\n"
                if len(datos['citas']) > 5:
                    respuesta += f"📌 *... y {len(datos['citas']) - 5} citas más (ver listado completo)*\n"
        
        elif 'especialidades' in datos and isinstance(datos['especialidades'], list):
            respuesta += f"🏥 **Total especialidades:** {datos.get('total_especialidades', len(datos['especialidades']))}\n\n"
            respuesta += "📋 **Lista de especialidades:**\n"
            formulario_url = "/core/especialidades/"  # Ver especialidades
            for esp in datos['especialidades']:
                respuesta += f"   • {esp['nombre']} ({esp['num_doctores']} doctores)\n"
        
        elif 'medicamentos_frecuentes' in datos:
            respuesta += "💊 **Medicamentos más recetados:**\n"
            formulario_url = "/core/medicamentos/"  # Ver medicamentos
            for i, med in enumerate(datos['medicamentos_frecuentes'][:10], 1):
                respuesta += f"   {i}. {med['medicamento__nombre']} - {med['veces_recetado']} veces\n"
        
        elif 'diagnosticos_frecuentes' in datos:
            respuesta += "🩺 **Diagnósticos más frecuentes:**\n"
            formulario_url = "/core/diagnosticos/"  # Ver diagnósticos
            for i, diag in enumerate(datos['diagnosticos_frecuentes'][:10], 1):
                respuesta += f"   {i}. {diag['diagnostico__nombre']} - {diag['frecuencia']} casos\n"
        
        elif 'total_ingresos' in datos:
            respuesta += f"💰 **Ingresos de {datos['mes']}/{datos['año']}:** ${datos['total_ingresos']:,.2f}\n"
            respuesta += f"📄 **Número de pagos:** {datos['numero_pagos']}\n"
            formulario_url = "/doctor/pago/"  # Ver pagos
        
        elif 'pacientes_encontrados' in datos:
            respuesta += f"🔍 **Pacientes encontrados:** {datos['total']}\n"
            formulario_url = "/core/pacientes/"  # Ver pacientes
            for paciente in datos['pacientes_encontrados'][:5]:
                respuesta += f"   • {paciente['nombres']} {paciente['apellidos']} - {paciente['cedula_ecuatoriana']}\n"
        
        elif 'doctores_encontrados' in datos:
            respuesta += f"🔍 **Doctores encontrados:** {datos['total']}\n"
            formulario_url = "/core/doctores/"  # Ver doctores
            for doctor in datos['doctores_encontrados'][:5]:
                respuesta += f"   • Dr. {doctor['nombres']} {doctor['apellidos']} - {doctor['especialidad__nombre']}\n"
        
        elif 'pacientes' in datos and 'total_pacientes_nuevos' in datos:
            respuesta += f"👥 **Pacientes nuevos (últimos {datos['periodo_dias']} días):** {datos['total_pacientes_nuevos']}\n"
            formulario_url = "/core/pacientes/"  # Ver pacientes
        
        # Estadísticas generales del sistema
        elif 'pacientes' in datos and 'doctores' in datos:
            respuesta += f"👥 **Pacientes:** {datos['pacientes']['total']} (activos: {datos['pacientes']['activos']})\n"
            respuesta += f"👨‍⚕️ **Doctores:** {datos['doctores']['total']} (activos: {datos['doctores']['activos']})\n"
            respuesta += f"📅 **Citas:** {datos['citas']['total']} (hoy: {datos['citas']['hoy']}, pendientes: {datos['citas']['pendientes']})\n"
            respuesta += f"🩺 **Atenciones:** {datos['atenciones']['total']} (este mes: {datos['atenciones']['este_mes']})\n"
            respuesta += f"💊 **Medicamentos:** {datos['medicamentos']}\n"
            respuesta += f"🏥 **Especialidades:** {datos['especialidades']}\n"
            formulario_url = "/"  # Página principal
        
        else:
            # Respuesta genérica para datos no reconocidos
            respuesta += f"ℹ️ **Datos obtenidos exitosamente**\n"
            respuesta += f"📝 Consulta: {datos.get('consulta', 'Información del sistema')}\n"
        
        # NO agregar el enlace al texto - solo estará en el botón
        # El formulario_url se envía separado para que se use en el botón
        
        return {
            "accion": "consulta_bd",
            "datos": datos,
            "respuesta": respuesta.strip(),
            "confianza": 1.0,
            "necesita_aclaracion": False,
            "campos_faltantes": [],
            "formulario_url": formulario_url,
            "tiempo_respuesta": 0.1,
            "servicio": "Base de Datos Local"
        }
