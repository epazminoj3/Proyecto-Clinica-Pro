# -*- coding: utf-8 -*-
"""
Vistas del Chatbot IA para el Sistema Clínico
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .ia_engine_multi import ia_local, get_status_completo, cambiar_api_key_manual
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def procesar_mensaje(request):
    """
    Endpoint principal para procesar mensajes del chatbot
    Todos los usuarios autenticados pueden usar todas las funciones
    """
    try:
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'No autenticado',
                'respuesta': 'Debes iniciar sesión para usar el asistente IA.'
            }, status=401)
        
        # Parsear datos del request
        data = json.loads(request.body)
        mensaje = data.get('mensaje', '').strip()
        
        if not mensaje:
            return JsonResponse({
                'error': 'Mensaje vacío',
                'respuesta': 'Por favor, escribe algo para ayudarte.'
            }, status=400)
        
        logger.info(f"Mensaje recibido: {mensaje}")
        
        # NUEVO: Detectar consultas sobre cómo hacer una cita ANTES de procesar con IA
        mensaje_lower = mensaje.lower()
        
        # Patrones para detectar preguntas sobre procedimientos de citas
        patrones_como_hacer_cita = [
            r'c[oó]mo\s+(?:hago|hacer|agenda[rdo]?|programa[rdo]?|saco)\s+(?:una\s+)?cita',
            r'c[oó]mo\s+(?:puedo|debo)\s+(?:agenda[rdo]?|programa[rdo]?|hacer)\s+(?:una\s+)?cita',
            r'(?:cu[aá]les\s+son\s+)?(?:los\s+)?pasos\s+para\s+(?:agenda[rdo]?|programa[rdo]?|hacer)\s+(?:una\s+)?cita',
            r'qu[eé]\s+(?:necesito|debo\s+hacer)\s+para\s+(?:agenda[rdo]?|programa[rdo]?)\s+(?:una\s+)?cita',
            r'procedimiento\s+para\s+(?:agenda[rdo]?|programa[rdo]?)\s+(?:una\s+)?cita',
            r'gu[ií]a\s+para\s+(?:agenda[rdo]?|programa[rdo]?)\s+(?:una\s+)?cita',
            r'instrucciones\s+para\s+(?:agenda[rdo]?|programa[rdo]?)\s+(?:una\s+)?cita',
            r'ayuda\s+para\s+(?:agenda[rdo]?|programa[rdo]?)\s+(?:una\s+)?cita',
            r'explicar\s+c[oó]mo\s+(?:agenda[rdo]?|programa[rdo]?)\s+(?:una\s+)?cita'
        ]
        
        # Verificar si es una consulta sobre cómo hacer una cita
        for patron in patrones_como_hacer_cita:
            if re.search(patron, mensaje_lower):
                respuesta_pasos = generar_respuesta_pasos_cita()
                respuesta_pasos['timestamp'] = str(datetime.now())
                respuesta_pasos['usuario_mensaje'] = mensaje
                respuesta_pasos['grupo_usuario'] = request.user.groups.first().name if request.user.groups.exists() else 'Sin grupo'
                logger.info(f"Chatbot - Consulta sobre cómo hacer cita: {mensaje}")
                return JsonResponse(respuesta_pasos)
        
        # Verificar si IA está disponible
        if not ia_local.verificar_conexion():
            modelos_disponibles = ia_local.obtener_modelos_disponibles()
            
            # Verificar si el problema es por tokens agotados
            status_keys = ia_local.get_status_todas_las_keys()
            tokens_disponibles = status_keys.get('total_tokens_disponibles', 0)
            
            error_response = {
                'error': 'IA no disponible',
                'respuesta': 'El asistente IA no está disponible en este momento.',
                'estado': {
                    'modelo_requerido': ia_local.modelo,
                    'modelos_instalados': modelos_disponibles,
                    'tokens_disponibles': tokens_disponibles,
                    'total_keys': status_keys.get('total_keys', 0)
                }
            }
            
            # Mensajes específicos según el problema
            if tokens_disponibles <= 100:
                error_response['respuesta'] = '⚠️ IA temporalmente desconectada: Se han agotado los tokens diarios de todas las API keys de Groq.'
                error_response['instrucciones'] = [
                    'Los tokens se resetean automáticamente cada 24 horas',
                    'Puedes agregar más API keys de Groq para mayor capacidad',
                    'O esperar hasta mañana para continuar usando el asistente'
                ]
                error_response['tipo_error'] = 'tokens_agotados'
                error_response['tokens_restantes'] = tokens_disponibles
            elif not modelos_disponibles:
                error_response['respuesta'] = 'Groq está ejecutándose pero no hay modelos disponibles.'
                error_response['instrucciones'] = [
                    'Verifica tu conexión a internet',
                    'Revisa la configuración de la API Key de Groq'
                ]
                error_response['tipo_error'] = 'sin_modelos'
            elif ia_local.modelo not in modelos_disponibles:
                error_response['respuesta'] = f'El modelo {ia_local.modelo} no está disponible en Groq.'
                error_response['instrucciones'] = [
                    'Revisa la lista de modelos disponibles',
                    'O cambia el modelo en settings.py'
                ]
                error_response['tipo_error'] = 'modelo_no_disponible'
            else:
                error_response['respuesta'] = 'Error de conexión con Groq API.'
                error_response['instrucciones'] = [
                    'Verifica tu conexión a internet',
                    'Revisa la configuración de la API Key'
                ]
                error_response['tipo_error'] = 'conexion'
            
            return JsonResponse(error_response, status=503)

        logger.info("Iniciando procesamiento con IA...")
        
        # Procesar mensaje con IA
        resultado = ia_local.procesar_mensaje(mensaje)
        
        logger.info(f"Resultado obtenido: {type(resultado)}")
        
        # Agregar información adicional
        resultado['timestamp'] = str(datetime.now())
        resultado['usuario_mensaje'] = mensaje
        resultado['grupo_usuario'] = request.user.groups.first().name if request.user.groups.exists() else 'Sin grupo'
        
        # Log para debugging
        logger.info(f"Chatbot - Usuario: {mensaje} | IA: {resultado.get('accion', 'N/A')}")
        logger.info(f"URL generada: {resultado.get('formulario_url', 'No URL')}")
        logger.info(f"Datos extraídos: {resultado.get('datos', {})}")
        
        return JsonResponse(resultado)
        
    except json.JSONDecodeError as e:
        logger.error(f"Error JSON: {e}")
        return JsonResponse({
            'error': 'JSON inválido',
            'respuesta': 'Error en el formato de la solicitud.'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error en chatbot: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Error interno',
            'respuesta': 'Lo siento, ocurrió un error interno. Por favor, intenta de nuevo.',
            'detalles': str(e)
        }, status=500)

@login_required
def chat_interface(request):
    """
    Interfaz principal del chatbot
    Disponible para todos los usuarios autenticados con acceso completo
    """
    context = {
        'titulo': 'Asistente IA Clínico',
        'ia_disponible': ia_local.verificar_conexion(),
        'grupo_usuario': request.user.groups.first().name if request.user.groups.exists() else 'Sin grupo'
    }
    return render(request, 'chatbot/chat_interface.html', context)

@csrf_exempt
@require_http_methods(["GET"])
def estado_ia(request):
    """
    Endpoint para verificar el estado completo de la IA
    """
    disponible = ia_local.verificar_conexion()
    modelos = ia_local.obtener_modelos_disponibles()
    status_keys = ia_local.get_status_todas_las_keys()
    tokens_disponibles = status_keys.get('total_tokens_disponibles', 0)
    
    estado = {
        'disponible': disponible,
        'mensaje': 'IA Groq disponible y funcional' if disponible else 'IA Groq no disponible',
        'detalles': {
            'modelo_configurado': ia_local.modelo,
            'servicio': 'Groq Cloud API',
            'api_key_configurada': bool(getattr(ia_local, 'api_keys', None)),
            'modelos_disponibles': modelos,
            'modelo_disponible': ia_local.modelo in modelos if modelos else False,
            'tokens_disponibles': tokens_disponibles,
            'total_keys': status_keys.get('total_keys', 0),
            'limite_diario': ia_local.limite_tokens_por_key if hasattr(ia_local, 'limite_tokens_por_key') else 14000
        }
    }
    
    # Determinar tipo de error si no está disponible
    if not disponible:
        if tokens_disponibles <= 100:
            estado['detalles']['tipo_error'] = 'tokens_agotados'
            estado['mensaje'] = '⚠️ Tokens diarios agotados - Se resetean automáticamente cada 24 horas'
        elif not modelos:
            estado['detalles']['tipo_error'] = 'sin_modelos'
            estado['mensaje'] = 'Error: No hay modelos disponibles'
        elif ia_local.modelo not in modelos:
            estado['detalles']['tipo_error'] = 'modelo_no_disponible'
            estado['mensaje'] = f'Error: Modelo {ia_local.modelo} no disponible'
        else:
            estado['detalles']['tipo_error'] = 'conexion'
            estado['mensaje'] = 'Error de conexión con Groq API'
    
    # Agregar diagnóstico específico
    if not disponible:
        if not getattr(ia_local, 'api_key', None):
            estado['diagnostico'] = 'API Key de Groq no configurada'
            estado['solucion'] = 'Configura GROQ_API_KEY en las variables de entorno'
        elif not modelos:
            estado['diagnostico'] = 'No se pudieron obtener los modelos disponibles de Groq'
            estado['solucion'] = 'Verifica la conectividad a internet y la configuración de la API Key'
        else:
            estado['diagnostico'] = 'Error de conexión con Groq API'
            estado['solucion'] = 'Verifica tu conexión a internet y la validez de la API Key'
    
    return JsonResponse(estado)

@csrf_exempt
@require_http_methods(["POST"])
def generar_formulario(request):
    """
    Genera formulario pre-llenado basado en datos extraídos por IA
    """
    try:
        data = json.loads(request.body)
        accion = data.get('accion')
        datos = data.get('datos', {})
        
        # Generar parámetros para pre-llenar formulario
        params = []
        for key, value in datos.items():
            if value and value.strip():
                # Limpiar y formatear valor
                value_clean = str(value).strip()
                params.append(f"{key}={value_clean}")
        
        # URLs de formularios (CORREGIDAS)
        formularios = {
            'cita': '/doctor/cita_medica/crear/',
            'paciente': '/core/pacientes/crear/',
            'atencion': '/doctor/atenciones/crear/',
            'pago': '/doctor/pago/crear/',
            'medicamento': '/core/medicamentos/crear/',
            'doctor': '/core/doctores/crear/',
            'especialidad': '/core/especialidades/crear/',
            'horario': '/doctor/horario/crear/'
        }
        
        url_base = formularios.get(accion)
        if not url_base:
            return JsonResponse({
                'error': 'Acción no válida',
                'acciones_disponibles': list(formularios.keys())
            }, status=400)
        
        # Construir URL completa
        url_completa = url_base
        if params:
            url_completa += '?' + '&'.join(params)
        
        return JsonResponse({
            'url_formulario': url_completa,
            'accion': accion,
            'datos_prellenados': datos,
            'mensaje': f'Formulario de {accion} preparado con tus datos'
        })
        
    except Exception as e:
        logger.error(f"Error generando formulario: {e}")
        return JsonResponse({
            'error': 'Error generando formulario',
            'mensaje': 'No se pudo generar el formulario. Intenta de nuevo.'
        }, status=500)

from datetime import datetime

@login_required
@require_http_methods(["GET"])
def api_status_multikey(request):
    """
    Endpoint para obtener el estado de todas las API keys de Groq
    Solo para administradores y doctores
    """
    try:
        # Verificar permisos
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__icontains='doctor').exists() or
                request.user.groups.filter(name__icontains='admin').exists()):
            return JsonResponse({
                'error': 'Permisos insuficientes',
                'mensaje': 'Solo administradores y doctores pueden ver el estado de las API keys'
            }, status=403)
        
        # Obtener estado completo
        estado = get_status_completo()
        
        return JsonResponse({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': estado
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado multi-key: {e}")
        return JsonResponse({
            'error': 'Error interno',
            'mensaje': 'No se pudo obtener el estado de las API keys'
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def cambiar_api_key(request):
    """
    Endpoint para cambiar manualmente la API key activa
    Solo para administradores
    """
    try:
        # Verificar permisos de administrador
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__icontains='admin').exists()):
            return JsonResponse({
                'error': 'Permisos insuficientes',
                'mensaje': 'Solo administradores pueden cambiar la API key activa'
            }, status=403)
        
        data = json.loads(request.body)
        key_index = data.get('key_index')
        
        if key_index is None:
            return JsonResponse({
                'error': 'Parámetro requerido',
                'mensaje': 'Debe especificar el índice de la API key (key_index)'
            }, status=400)
        
        # Intentar cambiar la API key
        if cambiar_api_key_manual(key_index):
            return JsonResponse({
                'status': 'success',
                'mensaje': f'API key cambiada exitosamente al índice {key_index}',
                'timestamp': datetime.now().isoformat(),
                'new_key_index': key_index
            })
        else:
            return JsonResponse({
                'error': 'Cambio fallido',
                'mensaje': f'No se pudo cambiar a la API key con índice {key_index}'
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido',
            'mensaje': 'Formato de datos incorrecto'
        }, status=400)
    except Exception as e:
        logger.error(f"Error cambiando API key: {e}")
        return JsonResponse({
            'error': 'Error interno',
            'mensaje': 'No se pudo cambiar la API key'
        }, status=500)

@login_required
def admin_panel_multikey(request):
    """
    Panel de administración para el sistema multi-key
    Solo para administradores
    """
    try:
        # Verificar permisos de administrador
        if not (request.user.is_superuser or 
                request.user.groups.filter(name__icontains='admin').exists()):
            return render(request, 'chatbot/admin_panel.html', {
                'error': 'Permisos insuficientes',
                'mensaje': 'Solo administradores pueden acceder al panel de control'
            })
        
        # Obtener estado del sistema
        estado = get_status_completo()
        
        context = {
            'titulo': 'Panel de Control - Sistema Multi-Key Groq',
            'estado': estado,
            'timestamp': datetime.now().isoformat(),
            'usuario': request.user
        }
        
        return render(request, 'chatbot/admin_panel.html', context)
        
    except Exception as e:
        logger.error(f"Error en panel de administración: {e}")
        return render(request, 'chatbot/admin_panel.html', {
            'error': 'Error interno',
            'mensaje': f'Error cargando el panel: {str(e)}'
        })

def generar_respuesta_pasos_cita():
    """Genera respuesta con los pasos para agendar una cita médica"""
    respuesta = """📋 **Pasos para agendar una cita médica:**

**📝 Opción 1: Crear cita con el chatbot**
1️⃣ Escribe algo como: "Crear cita para el día [fecha] a las [hora] con el paciente [nombre]"
2️⃣ El sistema te generará un enlace pre-llenado con los datos
3️⃣ Haz clic en el botón "Ir al formulario" para completar el registro

**🖥️ Opción 2: Crear cita manualmente**
1️⃣ Ve al módulo de "Citas Médicas" en el menú principal
2️⃣ Haz clic en "Crear nueva cita"
3️⃣ Completa los siguientes datos:
   • 📅 **Fecha**: Selecciona el día de la cita
   • 🕐 **Hora**: Elige la hora disponible
   • 👤 **Paciente**: Busca o crea el paciente
   • 🏥 **Especialidad**: Selecciona la especialidad médica
   • 📝 **Observaciones**: Agrega notas adicionales (opcional)
4️⃣ Haz clic en "Guardar cita"

**📋 Datos necesarios del paciente:**
• Nombres y apellidos completos
• Número de cédula
• Teléfono de contacto
• Email (opcional)
• Fecha de nacimiento
• Sexo
• Dirección

**⚠️ Importante recordar:**
• Verificar disponibilidad de horarios
• Confirmar los datos del paciente
• Revisar que no haya conflictos de horarios
• El estado inicial será "Programada"

**💡 Consejo:** Puedes decirme "crear cita para mañana a las 10 am con Juan Pérez" y yo te ayudo a generar el formulario pre-llenado."""

    return {
        'respuesta': respuesta,
        'accion': 'consulta_bd',
        'datos': {
            'tipo_consulta': 'pasos_cita',
            'consulta': 'pasos para agendar una cita médica'
        },
        'confianza': 1.0,
        'necesita_aclaracion': False,
        'campos_faltantes': [],
        'formulario_url': '/doctor/cita_medica/crear/',
        'tipo_formulario': 'cita',
        'titulo_boton': 'Ir al formulario de citas'
    }
