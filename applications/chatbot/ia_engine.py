# -*- coding: utf-8 -*-
"""
Motor de IA con Groq para el Sistema Clínico
Utiliza Groq API para procesamiento de lenguaje natural ultrarrápido
"""

from groq import Groq
import json
import re
import os
from datetime import datetime, timedelta
from django.conf import settings
import logging
from .database_tools import DatabaseTools

logger = logging.getLogger(__name__)

class TokenMonitor:
    """Monitor de uso de tokens para Groq"""
    
    def __init__(self):
        self.archivo_log = os.path.join(settings.BASE_DIR, 'logs', 'tokens_usage.json')
        self.limite_diario = 14400  # Límite gratis de Groq
        
    def estimar_tokens(self, texto):
        """Estima tokens de un texto en español"""
        if not texto:
            return 0
        palabras = len(texto.split())
        caracteres = len(texto)
        return int(palabras * 1.3 + caracteres * 0.05)
    
    def cargar_log(self):
        """Carga el log de uso de tokens"""
        try:
            os.makedirs(os.path.dirname(self.archivo_log), exist_ok=True)
            with open(self.archivo_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"uso_diario": {}, "total_historico": 0}
    
    def guardar_log(self, log):
        """Guarda el log de uso de tokens"""
        try:
            os.makedirs(os.path.dirname(self.archivo_log), exist_ok=True)
            with open(self.archivo_log, 'w', encoding='utf-8') as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando log de tokens: {e}")
    
    def registrar_uso(self, entrada, respuesta, tokens_reales=None):
        """Registra el uso de tokens"""
        if tokens_reales:
            total_tokens = tokens_reales
        else:
            tokens_entrada = self.estimar_tokens(entrada)
            tokens_respuesta = self.estimar_tokens(respuesta)
            total_tokens = tokens_entrada + tokens_respuesta
        
        log = self.cargar_log()
        
        # Registrar uso del día actual
        hoy = datetime.now().strftime("%Y-%m-%d")
        if hoy not in log["uso_diario"]:
            log["uso_diario"][hoy] = 0
            
        log["uso_diario"][hoy] += total_tokens
        log["total_historico"] += total_tokens
        
        self.guardar_log(log)
        
        return {
            "tokens_usados": total_tokens,
            "tokens_dia": log["uso_diario"][hoy],
            "tokens_restantes": max(0, self.limite_diario - log["uso_diario"][hoy]),
            "porcentaje_usado": (log["uso_diario"][hoy] / self.limite_diario) * 100
        }
    
    def verificar_limite(self):
        """Verifica si podemos hacer más consultas hoy"""
        log = self.cargar_log()
        hoy = datetime.now().strftime("%Y-%m-%d")
        uso_hoy = log["uso_diario"].get(hoy, 0)
        
        return {
            "puede_continuar": uso_hoy < self.limite_diario,
            "tokens_usados": uso_hoy,
            "tokens_restantes": max(0, self.limite_diario - uso_hoy),
            "porcentaje": (uso_hoy / self.limite_diario) * 100
        }


class GroqIA:
    """Clase para manejar consultas a Groq AI"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GROQ_API_KEY', None)
        self.modelo = getattr(settings, 'GROQ_MODEL', 'llama3-8b-8192')
        self.monitor = TokenMonitor()
        self.db_tools = DatabaseTools()  # Herramientas de base de datos
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY no configurada. El chatbot no funcionará.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Cliente Groq inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente Groq: {e}")
                self.client = None
    
    def verificar_conexion(self):
        """Verifica si Groq está disponible y hay tokens suficientes"""
        if not self.client or not self.api_key:
            return False
            
        # Verificar límite de tokens
        limite_check = self.monitor.verificar_limite()
        if not limite_check["puede_continuar"]:
            logger.warning("Límite diario de tokens alcanzado")
            return False
            
        try:
            # Test simple para verificar conectividad
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model=self.modelo,
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"Error verificando conexión con Groq: {e}")
            return False
    
    def obtener_modelos_disponibles(self):
        """Obtiene lista de modelos disponibles en Groq"""
        return [
            "llama3-8b-8192",
            "llama3-70b-8192", 
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
    
    
    def procesar_mensaje(self, mensaje_usuario):
        """
        Procesa mensaje del usuario y extrae información médica
        """
        import time
        inicio_tiempo = time.time()
        
        try:
            logger.info(f"Procesando mensaje con Groq: {mensaje_usuario}")
            
            # Verificar límite de tokens
            limite_check = self.monitor.verificar_limite()
            if not limite_check["puede_continuar"]:
                return self._respuesta_limite_tokens(limite_check)
            
            # NUEVO: Detectar si es una consulta a base de datos
            resultado_db = self._procesar_consulta_bd(mensaje_usuario)
            if resultado_db:
                return resultado_db
            
            prompt = self._crear_prompt_medico(mensaje_usuario)
            
            logger.info("Consultando Groq API...")
            respuesta_ia, tokens_usados = self._consultar_groq(prompt)
            logger.info(f"Respuesta de Groq recibida")
            
            resultado = self._extraer_json_respuesta(respuesta_ia)
            logger.info(f"JSON extraído: {resultado.get('accion', 'N/A')}")
            
            # Validar y enriquecer respuesta
            resultado = self._validar_resultado(resultado, mensaje_usuario)
            
            # Agregar información de tiempo y tokens
            tiempo_respuesta = round(time.time() - inicio_tiempo, 2)
            resultado['tiempo_respuesta'] = tiempo_respuesta
            resultado['tokens_usados'] = tokens_usados
            resultado['servicio'] = 'Groq API'
            
            logger.info("Mensaje procesado exitosamente")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return self._respuesta_fallback(mensaje_usuario)
    
    def _consultar_groq(self, prompt):
        """Realiza consulta a Groq API"""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un asistente especializado en sistemas clínicos. Responde SOLO en formato JSON válido, sin texto adicional."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model=self.modelo,
                temperature=0.3,
                max_tokens=400,  # Limitar para ahorrar tokens
                top_p=0.9
            )
            
            respuesta_texto = response.choices[0].message.content
            
            # Registrar uso de tokens
            tokens_usados = response.usage.total_tokens
            self.monitor.registrar_uso(prompt, respuesta_texto, tokens_usados)
            
            logger.info(f"Tokens usados: {tokens_usados}")
            return respuesta_texto, tokens_usados
            
        except Exception as e:
            logger.error(f"Error consultando Groq: {e}")
            raise Exception(f"Error en Groq API: {str(e)}")
    
    def _respuesta_limite_tokens(self, limite_info):
        """Respuesta cuando se alcanza el límite de tokens"""
        return {
            "accion": "limite_tokens",
            "datos": {},
            "respuesta": f"📊 Límite diario alcanzado. Tokens usados: {limite_info['tokens_usados']}/14,400. Intenta mañana o contacta al administrador.",
            "confianza": 0.0,
            "necesita_aclaracion": True,
            "campos_faltantes": [],
            "formulario_url": None,
            "limite_info": limite_info
        }
    
    def _crear_prompt_medico(self, mensaje):
        """Crea prompt especializado para sistema clínico optimizado para Groq"""
        
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Prompt completamente reescrito para capturar todos los campos
        prompt = f"""Sistema clínico. FECHA: {fecha_hoy}

USUARIO: "{mensaje}"

Eres asistente médico especializado. Analiza y extrae TODOS los datos posibles.

MÓDULOS:
- paciente: registrar pacientes con datos completos
- doctor: registrar médicos 
- cita: agendar citas médicas
- atencion: consultas médicas
- medicamento: gestionar medicamentos
- diagnostico: diagnósticos médicos
- pago: facturación
- horario: horarios atención
- consulta: información general

CAMPOS PACIENTE:
nombres, apellidos, cedula, telefono, email, fecha_nacimiento (YYYY-MM-DD)
sexo (masculino/femenino), estado_civil (soltero/casado/divorciado/viudo)
tipo_sangre (O+/O-/A+/A-/B+/B-/AB+/AB-), direccion
antecedentes_personales, alergias, medicamentos_actuales

CAMPOS CITA:
fecha (YYYY-MM-DD), hora (HH:MM), especialidad, observaciones
estado (programada/confirmada/cancelada)

CAMPOS DOCTOR:
nombres, apellidos, cedula, especialidad, licencia_medica, telefono, email

CAMPOS MEDICAMENTO:
nombre, tipo, marca, dosis, precio, stock

FECHAS:
hoy = {fecha_hoy}
mañana = {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}

JSON FORMATO:
{{
    "accion": "accion_detectada",
    "datos": {{
        "nombres": "solo_nombres",
        "apellidos": "solo_apellidos",
        "cedula": "numero_cedula",
        "telefono": "telefono",
        "email": "email",
        "fecha_nacimiento": "YYYY-MM-DD",
        "sexo": "masculino_o_femenino",
        "estado_civil": "estado_exacto",
        "tipo_sangre": "tipo_exacto",
        "direccion": "direccion_completa",
        "fecha": "YYYY-MM-DD",
        "hora": "HH:MM",
        "especialidad": "especialidad_medica",
        "medicamento": "nombre_medicamento",
        "dosis": "dosis_medicamento",
        "diagnostico": "descripcion",
        "observaciones": "comentarios"
    }},
    "respuesta": "Respuesta natural específica",
    "confianza": 0.9,
    "necesita_aclaracion": false,
    "campos_faltantes": []
}}

REGLAS:
1. Extrae TODOS los datos mencionados
2. Usa valores exactos para campos de selección
3. Fechas en formato YYYY-MM-DD
4. Horas en formato HH:MM
5. Separa nombres y apellidos
6. Respuesta natural y específica

JSON:

Eres un asistente médico amigable. Analiza el mensaje y responde en JSON.

ACCIONES: cita, paciente, doctor, atencion, pago, consulta, medicamento, horario, diagnostico, especialidad, empleado, gasto, servicios, otro

FECHAS:
- hoy → {fecha_hoy}
- mañana → {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}

JSON formato:
{{
    "accion": "acción_identificada",
    "datos": {{
        "nombres": "solo_nombres",
        "apellidos": "solo_apellidos", 
        "paciente": "nombre_completo",
        "doctor": "nombre_doctor", 
        "fecha": "YYYY-MM-DD",
        "hora": "HH:MM",
        "cedula": "cedula",
        "telefono": "telefono",
        "email": "email",
        "direccion": "direccion",
        "especialidad": "especialidad",
        "diagnostico": "diagnostico",
        "medicamento": "medicamento",
        "sintomas": "sintomas",
        "observaciones": "detalles_adicionales"
    }},
    "respuesta": "Mensaje natural y específico sobre la acción (NO genérico, SÍ específico al contexto)",
    "confianza": 0.9,
    "necesita_aclaracion": false,
    "campos_faltantes": []
}}

IMPORTANTE: 
- "respuesta" debe ser específica al contexto, NO usar frases genéricas como "Procesando..."
- Si es un saludo/consulta general: usar acción "consulta" con respuesta amigable
- Si pide agregar paciente: usar acción "paciente" con respuesta confirmando los datos recibidos
- Ser natural, amigable y específico
"""
        return prompt
    
    def _extraer_json_respuesta(self, respuesta_texto):
        """Extrae JSON válido de la respuesta de Groq"""
        try:
            # Groq generalmente devuelve JSON limpio, pero verificamos
            texto_limpio = respuesta_texto.strip()
            
            # Buscar JSON en la respuesta
            inicio = texto_limpio.find('{')
            fin = texto_limpio.rfind('}') + 1
            
            if inicio == -1 or fin == 0:
                raise ValueError("No se encontró JSON en la respuesta")
            
            json_str = texto_limpio[inicio:fin]
            return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Error extrayendo JSON: {e}")
            return self._limpiar_y_extraer_json(respuesta_texto)
    
    def _limpiar_y_extraer_json(self, texto):
        """Intenta limpiar el texto y extraer JSON válido"""
        try:
            # Remover markdown y caracteres problemáticos
            texto_limpio = re.sub(r'```json|```', '', texto)
            texto_limpio = re.sub(r'\n\s*\n', '\n', texto_limpio)
            
            # Buscar patrón JSON más flexible
            patron = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(patron, texto_limpio, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
            
            raise ValueError("No se pudo extraer JSON válido")
            
        except Exception:
            # Fallback: crear respuesta básica
            return {
                "accion": "otro",
                "datos": {},
                "respuesta": "No pude procesar completamente tu solicitud. ¿Puedes ser más específico?",
                "confianza": 0.1,
                "necesita_aclaracion": True,
                "campos_faltantes": []
            }
    
    def _validar_resultado(self, resultado, mensaje_original):
        """Valida y enriquece el resultado"""
        # Asegurar campos obligatorios
        campos_requeridos = {
            "accion": "otro",
            "datos": {},
            "respuesta": "¡Hola! Estoy aquí para ayudarte con el sistema clínico. ¿En qué puedo asistirte?",
            "confianza": 0.5,
            "necesita_aclaracion": False,
            "campos_faltantes": []
        }
        
        for campo, valor_default in campos_requeridos.items():
            if campo not in resultado:
                resultado[campo] = valor_default
        
        # Evitar respuestas genéricas poco útiles
        respuestas_genericas = [
            "Procesando tu solicitud...",
            "Procesando...",
            "Un momento...",
            "Entendido...",
            "Perfecto...",
            "..."
        ]
        
        if resultado["respuesta"] in respuestas_genericas:
            if resultado["accion"] == "paciente":
                resultado["respuesta"] = "Perfecto, te ayudo a registrar un nuevo paciente. ¿Podrías proporcionarme más detalles como la cédula, teléfono o fecha de nacimiento?"
            elif resultado["accion"] == "cita":
                resultado["respuesta"] = "Entendido, vamos a agendar una cita médica. ¿Para qué fecha y hora te gustaría programarla?"
            elif resultado["accion"] == "consulta":
                resultado["respuesta"] = "¡Hola! Estoy aquí para ayudarte con cualquier consulta sobre el sistema clínico. ¿Qué necesitas?"
            else:
                resultado["respuesta"] = "Entiendo tu solicitud. ¿Podrías darme más detalles para ayudarte mejor?"
        
        # Validar acción
        acciones_validas = [
            "cita", "paciente", "doctor", "atencion", "pago", "consulta", 
            "medicamento", "horario", "diagnostico", "especialidad", 
            "empleado", "gasto", "servicios", "otro"
        ]
        if resultado["accion"] not in acciones_validas:
            resultado["accion"] = "otro"
        
        # Generar URL del formulario con parámetros pre-llenados si aplica
        resultado["formulario_url"] = self._generar_url_con_parametros(resultado["accion"], resultado["datos"])
        
        # Detectar campos faltantes para acciones específicas
        resultado["campos_faltantes"] = self._detectar_campos_faltantes(resultado)
        
        return resultado
    
    def _generar_url_formulario(self, accion):
        """Genera URL del formulario según la acción"""
        urls = {
            # Core module URLs - URLs exactas del sistema
            "cita": "/doctor/cita_medica/crear/",
            "paciente": "/core/pacientes/crear/",
            "doctor": "/core/doctores/crear/",
            "medicamento": "/core/medicamentos/crear/",
            "diagnostico": "/core/diagnosticos/crear/",
            "especialidad": "/core/especialidades/crear/",
            "tipo_sangre": "/core/tipo_sangre/crear/",
            "empleado": "/core/empleados/crear/",
            "cargo": "/core/cargos/crear/",
            "gasto": "/core/gasto_mensual/crear/",
            "marca_medicamento": "/core/marca_medicamento/crear/",
            "tipo_medicamento": "/core/tipo_medicamento/crear/",
            "tipo_gasto": "/core/tipo_gasto/crear/",
            
            # Doctor module URLs - URLs exactas del sistema
            "atencion": "/doctor/atenciones/crear/",
            "detalle_atencion": "/doctor/detalle_atencion/crear/",
            "pago": "/doctor/pago/crear/",
            "detalle_pago": "/doctor/detalle_pago/crear/",
            "horario": "/doctor/horario/crear/",
            "servicios": "/doctor/servicios_adicionales/crear/",
        }
        return urls.get(accion)

    def _generar_url_con_parametros(self, accion, datos):
        """Genera URL con parámetros para pre-llenar formulario"""
        url_base = self._generar_url_formulario(accion)
        if not url_base:
            return None
        
        # Procesar datos específicos según la acción
        if accion == "paciente":
            datos = self._procesar_datos_paciente(datos.copy())
        
        # Mapeo completo de campos para todos los formularios del sistema
        mapeo_campos = {
            # PACIENTES - Campos completos del modelo
            "nombres": "nombres",
            "apellidos": "apellidos", 
            "cedula": "cedula_ecuatoriana",
            "telefono": "telefono",
            "email": "email",
            "fecha_nacimiento": "fecha_nacimiento",
            "sexo": "sexo",
            "estado_civil": "estado_civil",
            "direccion": "direccion",
            "tipo_sangre": "tipo_sangre",
            "antecedentes_personales": "antecedentes_personales",
            "antecedentes_quirurgicos": "antecedentes_quirurgicos",
            "antecedentes_familiares": "antecedentes_familiares",
            "alergias": "alergias",
            "medicamentos_actuales": "medicamentos_actuales",
            "habitos_toxicos": "habitos_toxicos",
            "vacunas": "vacunas",
            
            # CITAS MÉDICAS
            "fecha": "fecha",
            "hora": "hora_cita",
            "hora_cita": "hora_cita",
            "estado": "estado",
            "observaciones": "observaciones",
            "paciente": "paciente",
            
            # DOCTORES
            "especialidad": "especialidad",
            "licencia_medica": "licencia_medica",
            "doctor": "nombres",
            
            # MEDICAMENTOS
            "medicamento": "nombre",
            "nombre": "nombre",
            "tipo": "tipo",
            "marca": "marca",
            "dosis": "dosis",
            "precio": "precio",
            "stock": "stock",
            "descripcion": "descripcion",
            
            # DIAGNÓSTICOS
            "diagnostico": "nombre",
            "sintomas": "sintomas"
        }
        
        # Construir parámetros de URL (evitar duplicados)
        parametros_dict = {}
        for campo_dato, valor in datos.items():
            if valor and str(valor).strip():
                campo_formulario = mapeo_campos.get(campo_dato, campo_dato)
                valor_limpio = str(valor).strip()
                # Solo agregar si no existe ya o si es más específico
                if campo_formulario not in parametros_dict:
                    parametros_dict[campo_formulario] = valor_limpio
        
        # Convertir a lista de parámetros
        parametros = [f"{campo}={valor}" for campo, valor in parametros_dict.items()]
        
        # Construir URL completa
        if parametros:
            url_completa = f"{url_base}?{'&'.join(parametros)}"
        else:
            url_completa = url_base
            
        return url_completa
    
    def _detectar_campos_faltantes(self, resultado):
        """Detecta qué campos faltan para completar la acción"""
        accion = resultado["accion"]
        datos = resultado["datos"]
        faltantes = []
        
        if accion == "cita":
            if not datos.get("paciente"):
                faltantes.append("paciente")
            if not datos.get("doctor"):
                faltantes.append("doctor")
            if not datos.get("fecha"):
                faltantes.append("fecha")
            if not datos.get("hora"):
                faltantes.append("hora")
        
        elif accion == "paciente":
            if not datos.get("paciente"):
                faltantes.append("nombre")
            if not datos.get("cedula"):
                faltantes.append("cedula")
        
        return faltantes
    
    def _respuesta_fallback(self, mensaje_original):
        """Respuesta cuando falla la IA de Groq"""
        return {
            "accion": "otro",
            "datos": {},
            "respuesta": "Lo siento, hay un problema con el asistente IA. Por favor, intenta de nuevo o usa los formularios directamente.",
            "confianza": 0.0,
            "necesita_aclaracion": True,
            "campos_faltantes": [],
            "formulario_url": None,
            "error": "Groq IA no disponible"
        }
    
    def _generar_respuesta_informativa(self, accion, datos):
        """Genera respuestas informativas para usuarios no-doctores"""
        respuestas_info = {
            "paciente": f"Te puedo proporcionar información sobre el registro de pacientes. En nuestro sistema clínico, los pacientes se registran con datos como: nombre completo, cédula, teléfono, dirección, fecha de nacimiento, tipo de sangre y contacto de emergencia. Para registrar un paciente nuevo, un doctor debe acceder al formulario correspondiente.",
            
            "cita": f"Las citas médicas en nuestro sistema incluyen: fecha, hora, paciente, doctor, especialidad, tipo de cita y observaciones. Las citas se pueden programar con anticipación y el sistema permite gestionar horarios disponibles.",
            
            "doctor": f"Los doctores en el sistema tienen información como: nombre, especialidad, número de licencia, teléfono, email y horarios de atención. Cada doctor puede tener múltiples especialidades.",
            
            "medicamento": f"El sistema gestiona medicamentos con: nombre, tipo, marca, dosis, indicaciones, contraindicaciones y stock disponible. Solo personal autorizado puede gestionar el inventario.",
            
            "atencion": f"Las atenciones médicas registran: fecha de atención, paciente, doctor, diagnóstico, tratamiento, medicamentos recetados y próxima cita.",
            
            "especialidad": f"Las especialidades médicas disponibles incluyen áreas como: medicina general, cardiología, pediatría, ginecología, traumatología, entre otras.",
            
            "horario": f"Los horarios de atención se configuran por doctor e incluyen: días de la semana, hora de inicio, hora de fin y duración de cada cita.",
            
            "pago": f"El sistema de pagos registra: monto, fecha, tipo de pago, concepto, paciente y estado del pago. Se pueden generar reportes financieros.",
        }
        
        return respuestas_info.get(accion, f"Puedo proporcionarte información general sobre {accion} en el sistema clínico. ¿Qué específicamente te gustaría saber?")
    
    def _procesar_datos_paciente(self, datos):
        """Procesa datos de paciente para separar nombres y apellidos y validar campos"""
        
        # Procesar nombre completo si existe
        if "paciente" in datos and datos["paciente"]:
            nombre_completo = datos["paciente"]
            partes = nombre_completo.strip().split()
            if len(partes) >= 2:
                mitad = len(partes) // 2
                datos["nombres"] = " ".join(partes[:mitad])
                datos["apellidos"] = " ".join(partes[mitad:])
            elif len(partes) == 1:
                datos["nombres"] = partes[0]
                datos["apellidos"] = ""
        
        # Normalizar campos de selección
        campos_normalizacion = {
            "sexo": {
                "masculino": "masculino", "hombre": "masculino", "m": "masculino", "male": "masculino",
                "femenino": "femenino", "mujer": "femenino", "f": "femenino", "female": "femenino"
            },
            "estado_civil": {
                "soltero": "soltero", "soltera": "soltero", "single": "soltero",
                "casado": "casado", "casada": "casado", "married": "casado",
                "divorciado": "divorciado", "divorciada": "divorciado", "divorced": "divorciado",
                "viudo": "viudo", "viuda": "viudo", "widow": "viudo"
            },
            "tipo_sangre": {
                "o+": "O+", "o positivo": "O+", "o pos": "O+",
                "o-": "O-", "o negativo": "O-", "o neg": "O-",
                "a+": "A+", "a positivo": "A+", "a pos": "A+",
                "a-": "A-", "a negativo": "A-", "a neg": "A-",
                "b+": "B+", "b positivo": "B+", "b pos": "B+",
                "b-": "B-", "b negativo": "B-", "b neg": "B-",
                "ab+": "AB+", "ab positivo": "AB+", "ab pos": "AB+",
                "ab-": "AB-", "ab negativo": "AB-", "ab neg": "AB-"
            }
        }
        
        # Aplicar normalización
        for campo, mapeo in campos_normalizacion.items():
            if campo in datos and datos[campo]:
                valor_original = str(datos[campo]).lower().strip()
                datos[campo] = mapeo.get(valor_original, datos[campo])
        
        # Procesar fechas
        if "edad" in datos and datos["edad"]:
            try:
                edad = int(datos["edad"])
                fecha_nacimiento = datetime.now() - timedelta(days=edad * 365)
                datos["fecha_nacimiento"] = fecha_nacimiento.strftime("%Y-%m-%d")
            except:
                pass
        
        return datos

    def _procesar_consulta_bd(self, mensaje):
        """Detecta y procesa consultas que requieren acceso a base de datos"""
        mensaje_lower = mensaje.lower()
        
        # Patrones que indican consulta a BD - EXPANDIDOS
        patrones_bd = [
            r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:cita|citas)',
            r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:paciente|pacientes)',
            r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:doctor|doctores|m[eé]dico|m[eé]dicos)',
            r'(?:cita|citas)\s+(?:de\s+)?(?:hoy|ma[ñn]ana|ayer|pasado\s+ma[ñn]ana)',
            r'(?:cita|citas)\s+(?:pr[oó]xima|pr[oó]ximas)',
            r'estad[ií]stica[s]?\s+(?:del\s+)?(?:sistema|general)',
            r'(?:buscar|encontrar|busca)\s+(?:paciente|doctor|m[eé]dico)',
            r'(?:medicamento|medicamentos)\s+(?:m[aá]s\s+)?(?:usado|usados|recetado|recetados)',
            r'(?:diagn[oó]stico|diagn[oó]sticos)\s+(?:m[aá]s\s+)?(?:com[uú]n|comunes|frecuente)',
            r'ingreso[s]?\s+(?:del\s+)?(?:mes|mensual)',
            r'especialidad(?:es)?',
            r'(?:listar|mostrar|ver)\s+(?:especialidad|especialidades)',
            r'(?:paciente|pacientes)\s+(?:nuevo|nuevos|reciente)',
            r'total\s+(?:de\s+)?(?:cita|citas|paciente|pacientes|doctor|doctores)',
            
            # NUEVOS PATRONES PARA FECHAS RELATIVAS Y HISTORIALES
            r'(?:qu[eé])\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:hoy|ma[ñn]ana|ayer|pasado\s+ma[ñn]ana)',
            r'(?:qu[eé])\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:el\s+)?\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'(?:qu[eé])\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:el\s+)?\d{4}-\d{1,2}-\d{1,2}',
            r'(?:hubo|tuve|tengo|tienen?)\s+(?:cita|citas)\s+(?:ayer|hoy|ma[ñn]ana)',
            r'(?:historial|historia)\s+(?:del?\s+)?(?:cita|citas)\s+(?:del?\s+)?(?:paciente)',
            r'(?:mostrar|ver|dame)\s+(?:el\s+)?(?:historial|historia)\s+(?:del?\s+)?(?:paciente)',
            r'(?:programada|programado)\s+(?:para\s+)?(?:hoy|ma[ñn]ana|ayer)',
            r'(?:cita|citas)\s+(?:del?\s+)?(?:paciente)\s+(?:con\s+)?(?:id|ID)\s+\d+',
            r'(?:para\s+)?(?:ma[ñn]ana|hoy|ayer)',
            r'(?:el\s+)?(?:d[ií]a\s+)?(?:de\s+)?(?:hoy|ma[ñn]ana|ayer)',
        ]
        
        # Verificar si coincide con algún patrón
        for patron in patrones_bd:
            if re.search(patron, mensaje_lower):
                return self._ejecutar_consulta_inteligente(mensaje)
        
        return None
    
    def _ejecutar_consulta_inteligente(self, mensaje):
        """Ejecuta consulta a BD basada en análisis inteligente del mensaje"""
        mensaje_lower = mensaje.lower()
        
        try:
            # NUEVOS PATRONES PARA FECHAS RELATIVAS Y HISTORIALES
            
            # Patrón para historial de citas de paciente
            if re.search(r'(?:historial|historia)\s+(?:del?\s+)?(?:cita|citas)\s+(?:del?\s+)?(?:paciente)', mensaje_lower) or \
               re.search(r'(?:mostrar|ver|dame)\s+(?:el\s+)?(?:historial|historia)\s+(?:del?\s+)?(?:paciente)', mensaje_lower) or \
               re.search(r'(?:cita|citas)\s+(?:del?\s+)?(?:paciente)\s+(?:con\s+)?(?:id|ID)\s+\d+', mensaje_lower):
                
                # Extraer ID del paciente
                match_id = re.search(r'(?:id|ID)\s+(\d+)', mensaje)
                if match_id:
                    paciente_id = int(match_id.group(1))
                    datos = self.db_tools.ejecutar_herramienta('historial_citas_paciente', {'paciente_id': paciente_id})
                    return self.db_tools.formatear_respuesta_bd(datos, f"Historial de citas del paciente ID {paciente_id}")
                else:
                    return {
                        "accion": "consulta_bd_error",
                        "datos": {},
                        "respuesta": "❓ Para mostrar el historial de citas, necesito que especifiques el ID del paciente. Por ejemplo: 'Historial del paciente con ID 1'",
                        "confianza": 0.5,
                        "necesita_aclaracion": True,
                        "campos_faltantes": ["paciente_id"],
                        "formulario_url": None
                    }
            
            # Patrón para citas por fecha relativa (mañana, ayer, hoy)
            elif re.search(r'(?:qu[eé])\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:hoy|ma[ñn]ana|ayer|pasado\s+ma[ñn]ana)', mensaje_lower) or \
                 re.search(r'(?:hubo|tuve|tengo|tienen?)\s+(?:cita|citas)\s+(?:ayer|hoy|ma[ñn]ana)', mensaje_lower) or \
                 re.search(r'(?:programada|programado)\s+(?:para\s+)?(?:hoy|ma[ñn]ana|ayer)', mensaje_lower) or \
                 re.search(r'(?:para\s+)?(?:ma[ñn]ana|hoy|ayer)', mensaje_lower):
                
                # Convertir palabras a fechas
                fecha_objetivo = None
                hoy = datetime.now().date()
                
                if 'hoy' in mensaje_lower:
                    fecha_objetivo = hoy
                elif 'mañana' in mensaje_lower or 'ma\u00f1ana' in mensaje_lower:
                    fecha_objetivo = hoy + timedelta(days=1)
                elif 'ayer' in mensaje_lower:
                    fecha_objetivo = hoy - timedelta(days=1)
                elif 'pasado mañana' in mensaje_lower or 'pasado ma\u00f1ana' in mensaje_lower:
                    fecha_objetivo = hoy + timedelta(days=2)
                
                if fecha_objetivo:
                    fecha_str = fecha_objetivo.strftime("%Y-%m-%d")
                    datos = self.db_tools.ejecutar_herramienta('citas_por_fecha', {'fecha': fecha_str})
                    
                    # Determinar título descriptivo
                    if fecha_objetivo == hoy:
                        titulo = "Citas programadas para hoy"
                    elif fecha_objetivo == hoy + timedelta(days=1):
                        titulo = "Citas programadas para mañana"
                    elif fecha_objetivo == hoy - timedelta(days=1):
                        titulo = "Citas que hubo ayer"
                    else:
                        titulo = f"Citas programadas para {fecha_objetivo.strftime('%d/%m/%Y')}"
                    
                    return self.db_tools.formatear_respuesta_bd(datos, titulo)
            
            # Patrón para citas por fecha específica (dd/mm/yyyy o yyyy-mm-dd)
            elif re.search(r'(?:qu[eé])\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:el\s+)?\d{1,2}[/-]\d{1,2}[/-]\d{4}', mensaje_lower) or \
                 re.search(r'(?:qu[eé])\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:el\s+)?\d{4}-\d{1,2}-\d{1,2}', mensaje_lower):
                
                # Extraer fecha del mensaje
                match_fecha = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', mensaje) or \
                             re.search(r'(\d{4}-\d{1,2}-\d{1,2})', mensaje)
                
                if match_fecha:
                    fecha_str = match_fecha.group(1)
                    # Convertir a formato estándar si es necesario
                    if '/' in fecha_str:
                        try:
                            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                            fecha_str = fecha_obj.strftime("%Y-%m-%d")
                        except:
                            try:
                                fecha_obj = datetime.strptime(fecha_str, "%m/%d/%Y")
                                fecha_str = fecha_obj.strftime("%Y-%m-%d")
                            except:
                                pass
                    
                    datos = self.db_tools.ejecutar_herramienta('citas_por_fecha', {'fecha': fecha_str})
                    return self.db_tools.formatear_respuesta_bd(datos, f"Citas programadas para {fecha_str}")
            
            # Análisis de intención original (resto de patrones)
            elif re.search(r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:cita|citas)', mensaje_lower):
                # Detectar filtros de estado
                estado = None
                if 'programada' in mensaje_lower or 'pendiente' in mensaje_lower:
                    estado = 'Programada'
                elif 'completada' in mensaje_lower or 'realizada' in mensaje_lower:
                    estado = 'Completada'
                elif 'cancelada' in mensaje_lower:
                    estado = 'Cancelada'
                
                datos = self.db_tools.ejecutar_herramienta('contar_citas', {'estado': estado} if estado else None)
                return self.db_tools.formatear_respuesta_bd(datos, f"Consulta sobre citas médicas")
            
            elif re.search(r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:paciente|pacientes)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('contar_pacientes')
                return self.db_tools.formatear_respuesta_bd(datos, "Consulta sobre pacientes")
            
            elif re.search(r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:doctor|doctores|m[eé]dico|m[eé]dicos)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('contar_doctores')
                return self.db_tools.formatear_respuesta_bd(datos, "Consulta sobre doctores")
            
            elif re.search(r'(?:cita|citas)\s+(?:de\s+)?(?:hoy)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('citas_hoy')
                return self.db_tools.formatear_respuesta_bd(datos, "Citas programadas para hoy")
            
            elif re.search(r'(?:cita|citas)\s+(?:pr[oó]xima|pr[oó]ximas)', mensaje_lower):
                # Detectar número de días
                dias = 7  # por defecto
                match_dias = re.search(r'(\d+)\s+d[ií]as?', mensaje_lower)
                if match_dias:
                    dias = int(match_dias.group(1))
                
                datos = self.db_tools.ejecutar_herramienta('citas_proximas', {'dias': dias})
                return self.db_tools.formatear_respuesta_bd(datos, f"Citas próximos {dias} días")
            
            elif re.search(r'estad[ií]stica[s]?\s+(?:del\s+)?(?:sistema|general)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('estadisticas_generales')
                return self.db_tools.formatear_respuesta_bd(datos, "Estadísticas generales del sistema")
            
            elif re.search(r'(?:buscar|encontrar|busca)\s+(?:paciente)', mensaje_lower):
                # Extraer criterio de búsqueda
                criterio = self._extraer_criterio_busqueda(mensaje)
                if criterio:
                    datos = self.db_tools.ejecutar_herramienta('buscar_paciente', {'criterio': criterio})
                    return self.db_tools.formatear_respuesta_bd(datos, f"Búsqueda de paciente: {criterio}")
                
            elif re.search(r'(?:buscar|encontrar|busca)\s+(?:doctor|m[eé]dico)', mensaje_lower):
                criterio = self._extraer_criterio_busqueda(mensaje)
                if criterio:
                    datos = self.db_tools.ejecutar_herramienta('buscar_doctor', {'criterio': criterio})
                    return self.db_tools.formatear_respuesta_bd(datos, f"Búsqueda de doctor: {criterio}")
            
            elif re.search(r'(?:medicamento|medicamentos)\s+(?:m[aá]s\s+)?(?:usado|usados|recetado|recetados)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('medicamentos_frecuentes')
                return self.db_tools.formatear_respuesta_bd(datos, "Medicamentos más recetados")
            
            elif re.search(r'(?:diagn[oó]stico|diagn[oó]sticos)\s+(?:m[aá]s\s+)?(?:com[uú]n|comunes|frecuente)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('diagnosticos_frecuentes')
                return self.db_tools.formatear_respuesta_bd(datos, "Diagnósticos más frecuentes")
            
            elif re.search(r'ingreso[s]?\s+(?:del\s+)?(?:mes|mensual)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('ingresos_mes')
                return self.db_tools.formatear_respuesta_bd(datos, "Ingresos del mes")
            
            elif re.search(r'especialidad(?:es)?|(?:listar|mostrar|ver)\s+(?:especialidad|especialidades)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('listar_especialidades')
                return self.db_tools.formatear_respuesta_bd(datos, "Especialidades médicas")
            
            elif re.search(r'(?:paciente|pacientes)\s+(?:nuevo|nuevos|reciente)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('pacientes_recientes')
                return self.db_tools.formatear_respuesta_bd(datos, "Pacientes registrados recientemente")
            
            # Si no coincide con patrones específicos pero es una consulta BD, mostrar estadísticas
            else:
                datos = self.db_tools.ejecutar_herramienta('estadisticas_generales')
                return self.db_tools.formatear_respuesta_bd(datos, "Información general del sistema")
                
        except Exception as e:
            logger.error(f"Error ejecutando consulta BD: {e}")
            return {
                "accion": "consulta_bd_error",
                "datos": {},
                "respuesta": f"❌ Error consultando la base de datos: {str(e)}",
                "confianza": 0.0,
                "necesita_aclaracion": False,
                "campos_faltantes": [],
                "formulario_url": None
            }
    
    def _extraer_criterio_busqueda(self, mensaje):
        """Extrae criterio de búsqueda del mensaje"""
        # Patrones para extraer nombres o cédulas
        patrones = [
            r'(?:buscar|encontrar|busca)\s+(?:paciente|doctor|médico)\s+(.+)',
            r'(?:paciente|doctor|médico)\s+(.+)',
            r'llamado\s+(.+)',
            r'nombre\s+(.+)',
            r'cédula\s+(.+)',
        ]
        
        for patron in patrones:
            match = re.search(patron, mensaje.lower())
            if match:
                criterio = match.group(1).strip()
                # Limpiar palabras comunes
                criterio = re.sub(r'\b(?:con|de|que|se|llama|llamado|llamada)\b', '', criterio).strip()
                if criterio and len(criterio) > 1:
                    return criterio
        
        return None

# Instancia global con Groq
groq_ia = GroqIA()

# Compatibilidad con código existente
ia_local = groq_ia
