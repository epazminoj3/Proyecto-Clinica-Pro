import os
import json
import time
import logging
import re
from datetime import datetime, timedelta
from groq import Groq
from .database_tools import DatabaseTools

logger = logging.getLogger(__name__)

class MultiGroqEngine:
    """Motor Groq con rotación automática de múltiples API keys"""
    
    def __init__(self):
        # CONFIGURACIÓN DE API KEYS - IMPORTANTE PARA NUEVA INSTALACIÓN
        # Para configurar en una nueva PC:
        # 1. Ve a https://console.groq.com/ y crea una cuenta gratuita
        # 2. Genera hasta 3 API keys (cada una da 14,400 tokens gratis por día)
        # 3. Reemplaza las keys de ejemplo abajo con tus keys reales
        # 4. Las keys reales empiezan con "gsk_" y son más largas
        
        # Lista de API keys de diferentes cuentas (REEMPLAZAR CON LAS TUYAS)
        self.api_keys = [
            "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",  # Cuenta 1 - REEMPLAZAR
            "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",  # Cuenta 2 - REEMPLAZAR  
            "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",  # Cuenta 3 - REEMPLAZAR
            # Agregar más keys aquí:
            "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",  # Cuenta 4 - Nueva key
            "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",  # Cuenta 5 - Nueva key
            "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",  # Cuenta 6 - Nueva key
            "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",  # Cuenta 7 - Nueva key
            "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",  # Cuenta 8 - Nueva key
            "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"
        ]
        
        self.current_key_index = 0
        self.modelo = 'llama3-8b-8192'
        self.limite_tokens_por_key = 14000  # Límite de seguridad por key
        self.usage_file = os.path.join(os.path.dirname(__file__), 'logs', 'multi_groq_usage.json')
        self.db_tools = DatabaseTools()  # Herramientas de base de datos
        
        # Crear directorio de logs si no existe
        os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
        
        logger.info(f"MultiGroqEngine inicializado con {len(self.api_keys)} API keys")
    
    def get_available_api_key(self):
        """Obtiene una API key disponible, rotando si es necesario"""
        usage = self.load_usage()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Intentar encontrar una key con tokens disponibles
        for i in range(len(self.api_keys)):
            key_index = (self.current_key_index + i) % len(self.api_keys)
            api_key = self.api_keys[key_index]
            
            key_usage = usage.get(api_key, {}).get(today, 0)
            
            if key_usage < self.limite_tokens_por_key:
                if i > 0:  # Si rotamos
                    self.current_key_index = key_index
                    logger.info(f"Rotando a API key #{key_index + 1} (tokens usados hoy: {key_usage})")
                
                return api_key, key_index
        
        # Si todas las keys están agotadas
        logger.warning("Todas las API keys han alcanzado el límite diario")
        return self.api_keys[self.current_key_index], self.current_key_index
    
    def load_usage(self):
        """Carga el registro de uso de tokens"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando usage: {e}")
        
        return {}
    
    def save_usage(self, api_key, tokens_used):
        """Guarda el uso de tokens por API key"""
        try:
            usage = self.load_usage()
            today = datetime.now().strftime("%Y-%m-%d")
            
            if api_key not in usage:
                usage[api_key] = {}
            if today not in usage[api_key]:
                usage[api_key][today] = 0
            
            usage[api_key][today] += tokens_used
            
            with open(self.usage_file, 'w') as f:
                json.dump(usage, f, indent=2)
                
            logger.debug(f"Tokens guardados: {tokens_used} para key #{self.get_key_number(api_key)}")
            
        except Exception as e:
            logger.error(f"Error guardando usage: {e}")
    
    def get_key_number(self, api_key):
        """Obtiene el número de la API key"""
        try:
            return self.api_keys.index(api_key) + 1
        except:
            return "?"
    
    def verificar_conexion(self):
        """Verifica si al menos una API key está disponible"""
        try:
            # Primero verificar si hay tokens disponibles
            usage = self.load_usage()
            today = datetime.now().strftime("%Y-%m-%d")
            
            tokens_disponibles = False
            for api_key in self.api_keys:
                key_usage = usage.get(api_key, {}).get(today, 0)
                if key_usage < self.limite_tokens_por_key:
                    tokens_disponibles = True
                    break
            
            # Si no hay tokens disponibles, retornar False
            if not tokens_disponibles:
                logger.warning("Todas las API keys han agotado sus tokens diarios")
                return False
            
            # Si hay tokens, probar conexión
            api_key, key_index = self.get_available_api_key()
            client = Groq(api_key=api_key)
            
            # Hacer una consulta simple de prueba
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model=self.modelo,
                max_tokens=10
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando conexión: {e}")
            return False
    
    def obtener_modelos_disponibles(self):
        """Obtiene lista de modelos disponibles"""
        try:
            api_key, _ = self.get_available_api_key()
            client = Groq(api_key=api_key)
            
            # Groq tiene modelos fijos disponibles
            return [
                'llama3-8b-8192',
                'llama3-70b-8192', 
                'mixtral-8x7b-32768',
                'gemma-7b-it'
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
            return []
    
    def procesar_mensaje(self, mensaje_usuario):
        """Procesa mensaje usando el sistema de múltiples API keys"""
        inicio_tiempo = time.time()
        
        try:
            logger.info(f"Procesando mensaje con MultiGroq: {mensaje_usuario}")
            
            # NUEVO: Detectar si es una consulta a base de datos
            resultado_db = self._procesar_consulta_bd(mensaje_usuario)
            if resultado_db:
                return resultado_db
            
            # Obtener API key disponible
            api_key, key_index = self.get_available_api_key()
            
            # Verificar si podemos continuar
            usage = self.load_usage()
            today = datetime.now().strftime("%Y-%m-%d")
            key_usage = usage.get(api_key, {}).get(today, 0)
            
            if key_usage >= self.limite_tokens_por_key:
                return self._respuesta_limite_tokens(key_usage, key_index)
            
            # Crear prompt y procesar
            prompt = self._crear_prompt_medico(mensaje_usuario)
            
            logger.info(f"Consultando Groq API with key #{key_index + 1}...")
            respuesta_ia, tokens_usados = self._consultar_groq(api_key, prompt)
            logger.info(f"Respuesta de Groq recibida (tokens: {tokens_usados})")
            
            # Procesar respuesta
            resultado = self._extraer_json_respuesta(respuesta_ia)
            logger.info(f"JSON extraído: {resultado.get('accion', 'N/A')}")
            
            resultado = self._validar_resultado(resultado, mensaje_usuario)
            
            # Guardar uso de tokens
            self.save_usage(api_key, tokens_usados)
            
            # Información adicional
            tiempo_respuesta = round(time.time() - inicio_tiempo, 2)
            resultado.update({
                'tiempo_respuesta': tiempo_respuesta,
                'tokens_usados': tokens_usados,
                'api_key_usada': key_index + 1,
                'tokens_restantes_key': self.limite_tokens_por_key - key_usage - tokens_usados,
                'servicio': f'Groq Multi-API (Key #{key_index + 1})'
            })
            
            logger.info("Mensaje procesado exitosamente")
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return self._respuesta_fallback(mensaje_usuario)
    
    def _consultar_groq(self, api_key, prompt):
        """Realiza consulta a Groq API con la key especificada"""
        try:
            client = Groq(api_key=api_key)
            
            response = client.chat.completions.create(
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
                max_tokens=800,
                top_p=1,
                stream=False
            )
            
            tokens_usados = response.usage.total_tokens
            respuesta_texto = response.choices[0].message.content
            
            logger.info(f"Tokens usados: {tokens_usados}")
            
            return respuesta_texto, tokens_usados
            
        except Exception as e:
            logger.error(f"Error en consulta Groq: {e}")
            raise
    
    def _respuesta_limite_tokens(self, uso_actual, key_index):
        """Respuesta cuando se alcanza el límite de tokens"""
        return {
            "accion": "consulta",
            "respuesta": f"API Key #{key_index + 1} ha alcanzado el límite diario ({uso_actual} tokens). El sistema intentará usar otra key automáticamente.",
            "confianza": 0.0,
            "necesita_aclaracion": True,
            "campos_faltantes": [],
            "formulario_url": None,
            "limite_alcanzado": True,
            "key_agotada": key_index + 1
        }
    
    def _respuesta_fallback(self, mensaje_usuario):
        """Respuesta de emergencia cuando falla todo"""
        return {
            "accion": "consulta",
            "respuesta": "Lo siento, hay un problema temporal con el servicio de IA. Por favor intenta de nuevo en unos momentos.",
            "confianza": 0.0,
            "necesita_aclaracion": True,
            "campos_faltantes": [],
            "formulario_url": None,
            "error_fallback": True
        }
    
    def get_status_todas_las_keys(self):
        """Obtiene el estado de todas las API keys"""
        usage = self.load_usage()
        today = datetime.now().strftime("%Y-%m-%d")
        
        status = []
        total_tokens_disponibles = 0
        
        for i, api_key in enumerate(self.api_keys):
            key_usage = usage.get(api_key, {}).get(today, 0)
            tokens_restantes = max(0, self.limite_tokens_por_key - key_usage)
            
            status.append({
                "key_number": i + 1,
                "tokens_usados": key_usage,
                "tokens_restantes": tokens_restantes,
                "porcentaje_uso": round((key_usage / self.limite_tokens_por_key) * 100, 1),
                "activa": i == self.current_key_index,
                "disponible": tokens_restantes > 100
            })
            
            total_tokens_disponibles += tokens_restantes
        
        return {
            "keys": status,
            "total_keys": len(self.api_keys),
            "total_tokens_disponibles": total_tokens_disponibles,
            "key_actual": self.current_key_index + 1,
            "fecha": today
        }

    def _crear_prompt_medico(self, mensaje):
        """Crea prompt especializado para sistema clínico optimizado para Groq"""
        
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Prompt completamente reescrito para capturar todos los campos
        prompt = f"""Sistema clínico. FECHA: {fecha_hoy}

USUARIO: "{mensaje}"

Eres asistente médico especializado. Analiza la intención del usuario y clasifica correctamente.

PRIORIDAD MÁXIMA - DETECCIÓN DE CREACIÓN:
Si el usuario menciona palabras como: "crear", "registrar", "nuevo", "nueva", "agendar", "agregar", "creame", "hazme", "programa"
SIEMPRE es una intención de CREACIÓN, independientemente de qué otros datos mencione.

EJEMPLOS:
- "crear doctor que se llame pedro sanchez con especialidades medicina general y pediatría" → accion: "doctor"
- "registrar paciente juan pérez con tipo de sangre O+" → accion: "paciente"  
- "nuevo medicamento llamado aspirina" → accion: "medicamento"
- "agendar cita para mañana con especialidad cardiología" → accion: "cita"
- "creame una cita para el dia 5 de junio a las 5 pm con el paciente erick pazmiño" → accion: "cita"

IMPORTANTE: Si detectas intención de CREAR, usa la acción específica (paciente/doctor/cita/medicamento).
Si es SOLO consulta informativa sin palabras de creación, usa "consulta".

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
fecha (YYYY-MM-DD), hora (HH:MM), paciente (nombre completo), especialidad, observaciones
estado (programada/confirmada/cancelada)

CAMPOS DOCTOR:
nombres, apellidos, cedula, especialidades (lista separada por comas), licencia_medica, telefono, email, fecha_nacimiento (YYYY-MM-DD), direccion

CAMPOS MEDICAMENTO:
nombre, tipo, marca, dosis, precio, stock

FECHAS:
hoy = {fecha_hoy}
mañana = {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}

CONVERSIÓN DE FECHAS:
- "5 de junio" → "2025-06-05"
- "junio 5" → "2025-06-05"
- "15 de diciembre" → "2025-12-15"
- "hoy" → {fecha_hoy}
- "mañana" → {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}

CONVERSIÓN DE HORAS:
- "5 pm" → "17:00"
- "5:30 pm" → "17:30"
- "10 am" → "10:00"
- "2:15 pm" → "14:15"
- "8:00" → "08:00"
- "15:30" → "15:30"

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
        "paciente": "nombre_completo_paciente",
        "especialidad": "especialidad_medica",
        "especialidades": "especialidad1, especialidad2",
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

REGLAS ESPECIALES:
1. SIEMPRE extrae TODOS los datos mencionados explícitamente
2. Para citas, busca específicamente: fecha, hora, paciente, especialidad
3. NO inventes datos que no están en el mensaje
4. Convierte fechas y horas al formato correcto
5. Para nombres de pacientes, extrae el nombre completo mencionado
6. Si dice "con el paciente X", extrae X como "paciente"
7. Si dice "para el día X", extrae X como "fecha"
8. Si dice "a las X", extrae X como "hora"

EJEMPLOS DE EXTRACCIÓN:
- "creame una cita para el dia 5 de junio a las 5 pm con el paciente erick pazmiño"
  → accion: "cita", fecha: "2025-06-05", hora: "17:00", paciente: "erick pazmiño"
  
- "registrar paciente juan pérez con tipo de sangre O+"
  → accion: "paciente", nombres: "juan", apellidos: "pérez", tipo_sangre: "O+"

- "agendar cita para mañana a las 10:30 am con especialidad cardiología"
  → accion: "cita", fecha: "{(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}", hora: "10:30", especialidad: "cardiología"

REGLA NOMBRES: Si hay múltiples palabras, las últimas 1-2 palabras van en apellidos, el resto en nombres.

JSON:"""
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
            import re
            
            # Buscar patrones JSON más flexibles
            json_patterns = [
                r'\{[^{}]*"accion"[^{}]*\}',
                r'\{.*?"accion".*?\}',
                r'\{.*\}'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, texto, re.DOTALL)
                for match in matches:
                    try:
                        return json.loads(match)
                    except:
                        continue
            
            # Si no se puede extraer, crear respuesta básica
            return {
                "accion": "consulta",
                "datos": {},
                "respuesta": "Lo siento, no pude procesar tu solicitud completamente. ¿Podrías reformularla?",
                "confianza": 0.3,
                "necesita_aclaracion": True,
                "campos_faltantes": []
            }
            
        except Exception as e:
            logger.error(f"Error en limpieza JSON: {e}")
            return self._respuesta_fallback("Error procesando respuesta")

    def _validar_resultado(self, resultado, mensaje_original):
        """Valida y enriquece el resultado de la IA"""
        
        # Campos requeridos básicos
        campos_requeridos = {
            "accion": "otro",
            "datos": {},
            "respuesta": "Procesando tu solicitud...",
            "confianza": 0.5,
            "necesita_aclaracion": False,
            "campos_faltantes": []
        }
        
        for campo, valor_default in campos_requeridos.items():
            if campo not in resultado:
                resultado[campo] = valor_default
        
        # Normalizar acciones de Groq a acciones del sistema
        accion_original = resultado["accion"].lower()
        mensaje_original_lower = mensaje_original.lower()
        
        # Mapeo expandido de acciones complejas a acciones simples
        if any(x in accion_original for x in ["registrar_paciente", "crear_paciente", "nuevo_paciente", "paciente"]):
            resultado["accion"] = "paciente"
        elif any(x in accion_original for x in ["registrar_doctor", "crear_doctor", "nuevo_doctor", "doctor"]):
            resultado["accion"] = "doctor"
        elif any(x in accion_original for x in ["agendar_cita", "crear_cita", "nueva_cita", "programar_cita", "cita"]):
            resultado["accion"] = "cita"
        elif any(x in accion_original for x in ["registrar_medicamento", "crear_medicamento", "medicamento"]):
            resultado["accion"] = "medicamento"
        elif any(x in accion_original for x in ["consulta_bd", "consultar_datos"]):
            resultado["accion"] = "consulta_bd"
        
        # Fallback: analizar el mensaje original si la acción no se detectó bien
        elif resultado["accion"] == "otro" or not resultado["accion"]:
            if any(x in mensaje_original_lower for x in ["crear paciente", "registrar paciente", "nuevo paciente"]):
                resultado["accion"] = "paciente"
            elif any(x in mensaje_original_lower for x in ["crear doctor", "registrar doctor", "nuevo doctor"]):
                resultado["accion"] = "doctor"
            elif any(x in mensaje_original_lower for x in ["crear cita", "agendar cita", "nueva cita"]):
                resultado["accion"] = "cita"
            elif any(x in mensaje_original_lower for x in ["crear medicamento", "registrar medicamento", "nuevo medicamento"]):
                resultado["accion"] = "medicamento"
        
        # Procesar datos según la acción
        if resultado["accion"] == "paciente":
            resultado["datos"] = self._procesar_datos_paciente(resultado["datos"])
        elif resultado["accion"] == "doctor":
            resultado["datos"] = self._procesar_datos_doctor(resultado["datos"])
        elif resultado["accion"] == "cita":
            resultado["datos"] = self._procesar_datos_cita(resultado["datos"])
        
        # Generar URL del formulario con parámetros pre-llenados si aplica
        resultado["formulario_url"] = self._generar_url_con_parametros(resultado["accion"], resultado["datos"])
        
        # Validar acción
        acciones_validas = [
            "cita", "paciente", "doctor", "atencion", "pago", "consulta", 
            "medicamento", "horario", "diagnostico", "especialidad", 
            "empleado", "gasto", "servicios", "otro"
        ]
        if resultado["accion"] not in acciones_validas:
            resultado["accion"] = "otro"
        
        return resultado

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

    def _procesar_datos_cita(self, datos):
        """Procesa datos de cita para manejar fechas, horas y nombres de pacientes"""
        
        # Procesar fecha si está en formato de texto
        if "fecha" in datos and datos["fecha"]:
            fecha_procesada = self._normalizar_fecha(datos["fecha"])
            if fecha_procesada:
                datos["fecha"] = fecha_procesada
        
        # Procesar hora si está en formato AM/PM
        if "hora" in datos and datos["hora"]:
            hora_procesada = self._normalizar_hora(datos["hora"])
            if hora_procesada:
                datos["hora"] = hora_procesada
        
        # Procesar nombre del paciente
        if "paciente" in datos and datos["paciente"]:
            nombre_completo = datos["paciente"].strip()
            partes = nombre_completo.split()
            
            if len(partes) >= 2:
                # Separar nombres y apellidos
                mitad = len(partes) // 2
                datos["paciente_nombres"] = " ".join(partes[:mitad])
                datos["paciente_apellidos"] = " ".join(partes[mitad:])
            elif len(partes) == 1:
                datos["paciente_nombres"] = partes[0]
                datos["paciente_apellidos"] = ""
            
            # Mantener el nombre completo también
            datos["paciente_completo"] = nombre_completo
        
        return datos

    def _normalizar_fecha(self, fecha_str):
        """Normaliza fecha de formato natural a YYYY-MM-DD"""
        if not fecha_str:
            return None
            
        fecha_str = fecha_str.lower().strip()
        
        # Si ya está en formato correcto
        if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha_str):
            return fecha_str
        
        # Mapeo de meses
        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        # Patrones de fecha
        try:
            # "5 de junio", "junio 5"
            for mes_nombre, mes_num in meses.items():
                patron1 = rf'(\d+)\s+de\s+{mes_nombre}'
                patron2 = rf'{mes_nombre}\s+(\d+)'
                
                match1 = re.search(patron1, fecha_str)
                match2 = re.search(patron2, fecha_str)
                
                if match1:
                    dia = int(match1.group(1))
                    return f"2025-{mes_num}-{dia:02d}"
                    
                if match2:
                    dia = int(match2.group(1))
                    return f"2025-{mes_num}-{dia:02d}"
            
            # "hoy"
            if fecha_str == "hoy":
                return datetime.now().strftime("%Y-%m-%d")
            
            # "mañana"
            if fecha_str == "mañana":
                return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
        except Exception as e:
            logger.warning(f"Error normalizando fecha '{fecha_str}': {e}")
            
        return None

    def _normalizar_hora(self, hora_str):
        """Normaliza hora de formato AM/PM a HH:MM"""
        if not hora_str:
            return None
            
        hora_str = hora_str.lower().strip()
        
        # Si ya está en formato correcto
        if re.match(r'^\d{1,2}:\d{2}$', hora_str):
            return hora_str
        
        try:
            # Patrones de hora
            if 'pm' in hora_str:
                # "5 pm", "5:30 pm"
                match = re.search(r'(\d+)(?::(\d+))?\s*pm', hora_str)
                if match:
                    hora = int(match.group(1))
                    minutos = int(match.group(2)) if match.group(2) else 0
                    
                    # Convertir a formato 24 horas
                    if hora != 12:
                        hora += 12
                    
                    return f"{hora:02d}:{minutos:02d}"
            
            elif 'am' in hora_str:
                # "10 am", "10:30 am"
                match = re.search(r'(\d+)(?::(\d+))?\s*am', hora_str)
                if match:
                    hora = int(match.group(1))
                    minutos = int(match.group(2)) if match.group(2) else 0
                    
                    # Manejar las 12 am (medianoche)
                    if hora == 12:
                        hora = 0
                    
                    return f"{hora:02d}:{minutos:02d}"
            
            else:
                # Solo número "17", "8:30"
                match = re.search(r'(\d+)(?::(\d+))?', hora_str)
                if match:
                    hora = int(match.group(1))
                    minutos = int(match.group(2)) if match.group(2) else 0
                    
                    return f"{hora:02d}:{minutos:02d}"
                    
        except Exception as e:
            logger.warning(f"Error normalizando hora '{hora_str}': {e}")
            
        return None

    def _procesar_datos_doctor(self, datos):
        """Procesa datos de doctor para manejar nombres, apellidos y especialidades"""
        
        # Procesar nombre completo si existe
        if "doctor" in datos and datos["doctor"]:
            nombre_completo = datos["doctor"]
            partes = nombre_completo.strip().split()
            if len(partes) >= 2:
                # Último elemento es apellido, el resto nombres
                datos["nombres"] = " ".join(partes[:-1])
                datos["apellidos"] = partes[-1]
            elif len(partes) == 1:
                datos["nombres"] = partes[0]
                datos["apellidos"] = ""
        
        # Si los nombres ya están separados correctamente, verificar si necesitan ajuste
        if "nombres" in datos and datos["nombres"] and not datos.get("apellidos"):
            nombre_completo = datos["nombres"]
            partes = nombre_completo.strip().split()
            if len(partes) >= 2:
                # Último elemento es apellido, el resto nombres
                datos["nombres"] = " ".join(partes[:-1])
                datos["apellidos"] = partes[-1]
        
        # Procesar especialidades múltiples
        if "especialidades" in datos and datos["especialidades"]:
            # Normalizar especialidades separadas por comas
            especialidades_str = datos["especialidades"]
            if isinstance(especialidades_str, str):
                # Limpiar y normalizar
                especialidades_lista = [esp.strip().title() for esp in especialidades_str.split(",")]
                datos["especialidad"] = ", ".join(especialidades_lista)  # Mapear a especialidad (singular)
                # Eliminar el campo plural para evitar confusión
                del datos["especialidades"]
        
        # Si solo hay una especialidad, asegurar que esté en el campo correcto
        if "especialidad" in datos and datos["especialidad"]:
            # Ya está en el campo correcto, solo normalizar
            if isinstance(datos["especialidad"], str):
                especialidades_lista = [esp.strip().title() for esp in datos["especialidad"].split(",")]
                datos["especialidad"] = ", ".join(especialidades_lista)
        
        return datos

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
        elif accion == "doctor":
            datos = self._procesar_datos_doctor(datos.copy())
        elif accion == "cita":
            datos = self._procesar_datos_cita(datos.copy())
        
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
            
            # CITAS MÉDICAS - Campos específicos del formulario
            "fecha": "fecha",
            "hora": "hora_cita",
            "hora_cita": "hora_cita",
            "estado": "estado",
            "observaciones": "observaciones",
            
            # CITAS - Campos para nuevo paciente (prefijo nuevo_)
            "paciente_nombres": "nuevo_nombres",
            "paciente_apellidos": "nuevo_apellidos",
            "paciente_cedula": "nuevo_cedula",
            "paciente_telefono": "nuevo_telefono",
            "paciente_email": "nuevo_email",
            "paciente_fecha_nacimiento": "nuevo_fecha_nacimiento",
            "paciente_sexo": "nuevo_sexo",
            "paciente_direccion": "nuevo_direccion",
            
            # DOCTORES
            "especialidad": "especialidad",
            "especialidades": "especialidad",  # Mapear plural a singular
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
        
        # Para citas, agregar parámetros especiales
        if accion == "cita":
            # Determinar si usar paciente existente o crear nuevo
            if datos.get('paciente_nombres') or datos.get('paciente_apellidos'):
                # Si tenemos nombres de paciente, usar modo nuevo
                parametros_dict['paciente_mode'] = 'new'
                
                # Agregar campos del nuevo paciente
                if datos.get('paciente_nombres'):
                    parametros_dict['nuevo_nombres'] = datos['paciente_nombres']
                if datos.get('paciente_apellidos'):
                    parametros_dict['nuevo_apellidos'] = datos['paciente_apellidos']
                    
                # Campos adicionales con valores por defecto
                parametros_dict['nuevo_cedula'] = ''  # Será llenado por el usuario
                parametros_dict['nuevo_telefono'] = ''
                parametros_dict['nuevo_fecha_nacimiento'] = ''
                parametros_dict['nuevo_sexo'] = ''
                parametros_dict['nuevo_direccion'] = ''
        
        # Mapear campos regulares
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
    
    def _procesar_consulta_bd(self, mensaje):
        """Detecta y procesa consultas que requieren acceso a base de datos"""
        mensaje_lower = mensaje.lower()
        
        # PRIMERO: Verificar si es una solicitud de CREACIÓN (prioridad máxima)
        # Si contiene palabras de creación, NO procesarlo como consulta BD
        palabras_creacion = ['crear', 'registrar', 'nuevo', 'nueva', 'agendar', 'agregar', 'añadir']
        if any(palabra in mensaje_lower for palabra in palabras_creacion):
            return None  # No es consulta BD, es creación
        
        # SEGUNDO: Verificar contexto de creación implícito
        # Si menciona datos específicos como nombres propios, emails, teléfonos, direcciones
        # es probable que sea creación aunque no use palabras explícitas
        indicadores_creacion = [
            r'[a-zA-Z]+@[a-zA-Z]+\.[a-zA-Z]+',  # emails
            r'\b\d{10,11}\b',  # teléfonos de 10-11 dígitos
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # nombres propios (Pedro Sanchez)
            r'que se llam[ea]',  # "que se llame"
            r'con el nombre',   # "con el nombre"
            r'su nombre es',    # "su nombre es"
        ]
        
        for patron in indicadores_creacion:
            if re.search(patron, mensaje):
                return None  # Probablemente es creación, no consulta
        
        # TERCERO: Patrones que indican consulta a BD (solo información)
        patrones_bd = [
            # Consultas básicas sobre citas hoy/mañana
            r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:hoy|ma[ñn]ana)',
            r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:tengo\s+)?(?:para\s+)?(?:hoy|ma[ñn]ana)',
            r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:tengo\s+)?(?:que\s+)?(?:tengo\s+)?(?:para\s+)?(?:hoy|ma[ñn]ana)',
            
            # Consultas con días de la semana
            r'cu[aá]nta[s]?\s+(?:hay\s+)?(?:de\s+)?(?:cita|citas)(?:\s+m[eé]dica[s]?)?\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:tengo\s+)?(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            
            # Consultas con fechas específicas
            r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:hay\s+|tengo\s+)?(?:para\s+el\s+)?(?:\d+\s+de\s+\w+|\w+\s+\d+)',
            r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:hay\s+|tengo\s+)?(?:para\s+)?(?:\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2})',
            
            # Consultas generales de citas
            r'cu[aá]nta[s]?\s+(?:hay\s+)?(?:de\s+)?(?:cita|citas)(?:\s+m[eé]dica[s]?)?(?!\s+(?:para|hoy|ma[ñn]ana))',
            
            # Consultas de otros elementos
            r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:paciente|pacientes)',
            r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:doctor|doctores|m[eé]dico|m[eé]dicos)',
            r'cu[aá]nta[s]?\s+(?:hay\s+)?(?:de\s+)?(?:especialidad|especialidades)',
            
            # Mostrar/listar citas
            r'(?:cita|citas)\s+(?:de\s+|para\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:cita|citas)\s+(?:del?\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            r'(?:cita|citas)\s+(?:del?\s+)?(?:\d+\s+de\s+\w+|\w+\s+\d+)',
            r'(?:cita|citas)\s+(?:para\s+)?(?:el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            
            # Consultas con "tengo"
            r'(?:que\s+)?(?:cita|citas)\s+(?:tengo|tiene[ns]?)\s+(?:para\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:que\s+)?(?:cita|citas)\s+(?:tengo|tiene[ns]?)\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            
            # Comandos de mostrar/ver con variantes
            r'(?:dime|muestra|ver)\s+(?:las?\s+)?(?:cita|citas)\s+(?:de\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:dime|muestra|ver)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo|tiene[ns]?)\s+(?:para\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:dime|muestra|ver)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo|tiene[ns]?)\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            r'(?:mostrar|enseñar|ver)\s+(?:las?\s+)?(?:cita|citas)\s+(?:de\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:dime|muestra|ver|mostrar)\s+(?:cu[aá]ntas?\s+)?(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:hoy|ma[ñn]ana)',
            
            # Comandos con muéstrame/enséñame
            r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:de\s+|para\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo|tiene[ns]?)\s+(?:para\s+)?(?:hoy|ma[ñn]ana)',
            r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo|tiene[ns]?)\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:del?\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)',
            r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:del?\s+|para\s+el\s+)?(?:\d+\s+de\s+\w+|\w+\s+\d+)',
            
            # Citas próximas
            r'(?:cita|citas)\s+(?:pr[oó]xima|pr[oó]ximas)',
            
            # Consultas del sistema
            r'estad[ií]stica[s]?\s+(?:del\s+)?(?:sistema|general)',
            r'(?:buscar|encontrar|busca)\s+(?:paciente|doctor|m[eé]dico)',
            r'(?:medicamento|medicamentos)\s+(?:m[aá]s\s+)?(?:usado|usados|recetado|recetados)',
            r'(?:diagn[oó]stico|diagn[oó]sticos)\s+(?:m[aá]s\s+)?(?:com[uú]n|comunes|frecuente)',
            r'ingreso[s]?\s+(?:del\s+)?(?:mes|mensual)',
            r'(?:listar|mostrar|ver)\s+(?:todas?\s+las?\s+)?(?:especialidad|especialidades)',
            r'(?:paciente|pacientes)\s+(?:nuevo|nuevos|reciente)',
            r'total\s+(?:de\s+)?(?:cita|citas|paciente|pacientes|doctor|doctores)',
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
            # Análisis de intención y extracción de parámetros
            
            # === CONSULTAS PARA HOY ===
            if re.search(r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:hay\s+)?(?:para\s+)?(?:hoy)', mensaje_lower) or re.search(r'(?:cita|citas)\s+(?:de\s+)?(?:hoy)', mensaje_lower) or re.search(r'(?:dime|muestra|ver|mostrar)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo\s+)?(?:de\s+)?(?:para\s+)?(?:hoy)', mensaje_lower) or re.search(r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:de\s+|para\s+)?(?:hoy)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('citas_hoy')
                return self.db_tools.formatear_respuesta_bd(datos, "Citas programadas para hoy")
            
            # === CONSULTAS PARA MAÑANA ===
            elif re.search(r'(?:cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:hay\s+|tengo\s+)?(?:para\s+)?(?:ma[ñn]ana)|(?:cita|citas)\s+(?:de\s+|para\s+)?(?:ma[ñn]ana)|(?:dime|muestra|ver|mostrar)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo\s+)?(?:para\s+)?(?:ma[ñn]ana)|(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo\s+)?(?:de\s+|para\s+)?(?:ma[ñn]ana))', mensaje_lower):
                fecha_manana = self._extraer_fecha_mensaje(mensaje)
                if fecha_manana:
                    datos = self.db_tools.ejecutar_herramienta('citas_por_fecha', {'fecha': fecha_manana})
                    return self.db_tools.formatear_respuesta_bd(datos, "Citas programadas para mañana")
                else:
                    # Fallback: calcular mañana manualmente
                    fecha_manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    datos = self.db_tools.ejecutar_herramienta('citas_por_fecha', {'fecha': fecha_manana})
                    return self.db_tools.formatear_respuesta_bd(datos, "Citas programadas para mañana")
            
            # === CONSULTAS PARA DÍAS DE LA SEMANA ===
            elif re.search(r'cu[aá]nta[s]?\s+(?:hay\s+)?(?:de\s+)?(?:cita|citas)(?:\s+m[eé]dica[s]?)?\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', mensaje_lower) or re.search(r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:tengo\s+)?(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', mensaje_lower) or re.search(r'(?:cita|citas)\s+(?:del?\s+|para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', mensaje_lower) or re.search(r'(?:dime|muestra|ver)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo|tiene[ns]?)\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', mensaje_lower) or re.search(r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:que\s+)?(?:tengo|tiene[ns]?)\s+(?:para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', mensaje_lower) or re.search(r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:del?\s+|para\s+el\s+)?(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo)', mensaje_lower):
                fecha_especifica = self._extraer_fecha_mensaje(mensaje)
                if fecha_especifica:
                    datos = self.db_tools.ejecutar_herramienta('citas_por_fecha', {'fecha': fecha_especifica})
                    return self.db_tools.formatear_respuesta_bd(datos, f"Citas programadas para {fecha_especifica}")
                else:
                    datos = self.db_tools.ejecutar_herramienta('citas_proximas', {'dias': 7})
                    return self.db_tools.formatear_respuesta_bd(datos, "Citas próximas")
            
            # === CONSULTAS PARA FECHAS ESPECÍFICAS ===
            elif re.search(r'cu[aá]nta[s]?\s+(?:cita|citas)\s+(?:hay\s+|tengo\s+)?(?:para\s+el\s+)?(?:\d+\s+de\s+\w+|\w+\s+\d+)',
                            mensaje_lower) or re.search(r'(?:cita|citas)\s+(?:del?\s+)?(?:\d+\s+de\s+\w+|\w+\s+\d+)', mensaje_lower) or re.search(r'(?:mu[eé]strame|ense[ñn]ame)\s+(?:las?\s+)?(?:cita|citas)\s+(?:del?\s+|para\s+el\s+)?(?:\d+\s+de\s+\w+|\w+\s+\d+)', mensaje_lower):
                fecha_especifica = self._extraer_fecha_mensaje(mensaje)
                if fecha_especifica:
                    datos = self.db_tools.ejecutar_herramienta('citas_por_fecha', {'fecha': fecha_especifica})
                    return self.db_tools.formatear_respuesta_bd(datos, f"Citas programadas para {fecha_especifica}")
                else:
                    # Si no se puede extraer la fecha, mostrar consulta general
                    datos = self.db_tools.ejecutar_herramienta('contar_citas')
                    return self.db_tools.formatear_respuesta_bd(datos, "Consulta sobre citas médicas")
            
            # === CONSULTAS GENERALES DE CITAS ===
            elif re.search(r'cu[aá]nta[s]?\s+(?:hay\s+)?(?:de\s+)?(?:cita|citas)(?:\s+m[eé]dica[s]?)?(?!\s+(?:para|hoy|ma[ñn]ana))', mensaje_lower):
                # Detectar filtros de estado para consultas generales
                estado = None
                if 'programada' in mensaje_lower or 'pendiente' in mensaje_lower:
                    estado = 'Programada'
                elif 'completada' in mensaje_lower or 'realizada' in mensaje_lower:
                    estado = 'Completada'
                elif 'cancelada' in mensaje_lower:
                    estado = 'Cancelada'
                
                datos = self.db_tools.ejecutar_herramienta('contar_citas', {'estado': estado} if estado else None)
                return self.db_tools.formatear_respuesta_bd(datos, f"Consulta sobre citas médicas")
            
            # === CONSULTAS DE OTROS ELEMENTOS ===
            elif re.search(r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:paciente|pacientes)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('contar_pacientes')
                return self.db_tools.formatear_respuesta_bd(datos, "Consulta sobre pacientes")
            
            elif re.search(r'cu[aá]nto[s]?\s+(?:hay\s+)?(?:de\s+)?(?:doctor|doctores|m[eé]dico|m[eé]dicos)', mensaje_lower):
                datos = self.db_tools.ejecutar_herramienta('contar_doctores')
                return self.db_tools.formatear_respuesta_bd(datos, "Consulta sobre doctores")
            
            # === CITAS PRÓXIMAS ===
            elif re.search(r'(?:cita|citas)\s+(?:pr[oó]xima|pr[oó]ximas)', mensaje_lower):
                # Detectar número de días
                dias = 7  # por defecto
                match_dias = re.search(r'(\d+)\s+d[ií]as?', mensaje_lower)
                if match_dias:
                    dias = int(match_dias.group(1))
                
                datos = self.db_tools.ejecutar_herramienta('citas_proximas', {'dias': dias})
                return self.db_tools.formatear_respuesta_bd(datos, f"Citas próximos {dias} días")
            
            # === ESTADÍSTICAS Y OTROS ===
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
            return None
    
    def _extraer_criterio_busqueda(self, mensaje):
        """Extrae criterio de búsqueda del mensaje"""
        # Patrones para extraer nombres, DNI, etc.
        patrones = [
            r'(?:llamado|llamada|con nombre|de nombre)\s+([A-Za-zÁ-ÿ\s]+)',
            r'(?:dni|cedula|documento)\s+(\d+)',
            r'(?:apellido)\s+([A-Za-zÁ-ÿ\s]+)',
        ]
        
        for patron in patrones:
            match = re.search(patron, mensaje, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extraer_fecha_mensaje(self, mensaje):
        """Extrae fecha del mensaje del usuario"""
        import re
        from datetime import datetime, timedelta
        
        mensaje_lower = mensaje.lower()
        hoy = datetime.now().date()
        
        # Patrones para fechas
        if re.search(r'\bhoy\b', mensaje_lower):
            return hoy.strftime("%Y-%m-%d")
        
        if re.search(r'\bma[ñn]ana\b', mensaje_lower):
            manana = hoy + timedelta(days=1)
            return manana.strftime("%Y-%m-%d")
        
        # Días de la semana
        dias_semana = {
            'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
            'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
        }
        
        for dia, numero in dias_semana.items():
            if dia in mensaje_lower:
                dias_hasta_dia = (numero - hoy.weekday()) % 7
                if dias_hasta_dia == 0:  # Es hoy
                    dias_hasta_dia = 7  # Próxima semana
                fecha_dia = hoy + timedelta(days=dias_hasta_dia)
                return fecha_dia.strftime("%Y-%m-%d")
        
        # Fechas específicas como "7 de julio", "julio 7", etc.
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Patrón "7 de julio" o "julio 7"
        for mes_nombre, mes_num in meses.items():
            patron1 = rf'(\d+)\s+de\s+{mes_nombre}'
            patron2 = rf'{mes_nombre}\s+(\d+)'
            
            match1 = re.search(patron1, mensaje_lower)
            match2 = re.search(patron2, mensaje_lower)
            
            if match1:
                dia = int(match1.group(1))
                try:
                    fecha = datetime(hoy.year, mes_num, dia).date()
                    return fecha.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
            if match2:
                dia = int(match2.group(1))
                try:
                    fecha = datetime(hoy.year, mes_num, dia).date()
                    return fecha.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        
        # Formato DD/MM/YYYY o DD-MM-YYYY
        patron_fecha = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(patron_fecha, mensaje)
        if match:
            dia, mes, año = match.groups()
            try:
                fecha = datetime(int(año), int(mes), int(dia)).date()
                return fecha.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        return None
