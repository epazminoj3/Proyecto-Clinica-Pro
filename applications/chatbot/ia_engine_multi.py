#!/usr/bin/env python3
"""
Motor de IA actualizado con sistema de múltiples API keys de Groq
Rotación automática para evitar límites de tokens
"""

import logging
from .multi_groq_engine import MultiGroqEngine

logger = logging.getLogger(__name__)

# Instancia global del motor multi-key
try:
    ia_local = MultiGroqEngine()
    logger.info("Motor MultiGroq inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando MultiGroqEngine: {e}")
    
    # Fallback al motor original en caso de error
    try:
        from .ia_engine import GroqIA
        ia_local = GroqIA()
        logger.warning("Usando motor original como fallback")
    except:
        logger.error("Error crítico: No se pudo inicializar ningún motor")
        ia_local = None

def get_status_completo():
    """Obtiene estado completo del sistema multi-key"""
    try:
        if ia_local and hasattr(ia_local, 'get_status_todas_las_keys'):
            return ia_local.get_status_todas_las_keys()
        else:
            # Fallback para motor original
            return {
                "keys": [{
                    "key_number": 1,
                    "tokens_usados": 0,
                    "tokens_restantes": 14400,
                    "porcentaje_uso": 0,
                    "activa": True,
                    "disponible": True
                }],
                "total_keys": 1,
                "total_tokens_disponibles": 14400,
                "key_actual": 1,
                "sistema": "motor_original"
            }
    except Exception as e:
        logger.error(f"Error obteniendo status: {e}")
        return {"error": str(e)}

def cambiar_api_key_manual(key_index):
    """Permite cambiar manualmente la API key activa"""
    try:
        if ia_local and hasattr(ia_local, 'current_key_index') and hasattr(ia_local, 'api_keys'):
            if 0 <= key_index < len(ia_local.api_keys):
                ia_local.current_key_index = key_index
                logger.info(f"API key cambiada manualmente a #{key_index + 1}")
                return True
        return False
    except Exception as e:
        logger.error(f"Error cambiando API key: {e}")
        return False

def test_todas_las_keys():
    """Prueba todas las API keys disponibles"""
    if not ia_local or not hasattr(ia_local, 'api_keys'):
        return {"error": "Motor multi-key no disponible"}
    
    resultados = []
    
    for i, api_key in enumerate(ia_local.api_keys):
        try:
            # Crear cliente temporal
            from groq import Groq
            client = Groq(api_key=api_key)
            
            # Hacer consulta de prueba
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model="llama3-8b-8192",
                max_tokens=10
            )
            
            resultados.append({
                "key_number": i + 1,
                "status": "FUNCIONAL",
                "tokens_test": response.usage.total_tokens
            })
            
        except Exception as e:
            resultados.append({
                "key_number": i + 1,
                "status": f"ERROR: {str(e)[:50]}...",
                "tokens_test": 0
            })
    
    return {
        "test_results": resultados,
        "keys_funcionales": len([r for r in resultados if "FUNCIONAL" in r["status"]]),
        "total_keys": len(resultados)
    }
