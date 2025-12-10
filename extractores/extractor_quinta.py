"""
Extractor de datos para Certificados de Quinta Categoría
Extrae: nombre y DNI
"""

import re
import pdfplumber
from pathlib import Path
from typing import Dict, Optional


def _determinar_resultado(nombre: Optional[str], dni: Optional[str], logger=None) -> tuple:
    """
    Determina éxito y observaciones basado en campos extraídos.
    
    Args:
        nombre: Nombre extraído o None
        dni: DNI extraído o None
        logger: Logger opcional para registro
        
    Returns:
        Tupla (exito: bool, observaciones: str)
    """
    if nombre and dni:
        if logger:
            logger.info("✅ QUINTA - Ambos campos extraídos correctamente")
        return True, "OK"
    
    elif nombre:
        if logger:
            logger.warning("⚠️ QUINTA - DNI no encontrado")
        return False, "DNI no encontrado"
    
    elif dni:
        if logger:
            logger.warning("⚠️ QUINTA - Nombre no encontrado")
        return False, "Nombre no encontrado"
    
    else:
        if logger:
            logger.warning("⚠️ QUINTA - No se encontró patrón de certificado de quinta")
        return False, "No se encontró patrón de certificado de quinta"


def extraer_datos_quinta(ruta_pdf: str, logger=None) -> Dict:
    """
    Extrae nombre y DNI de un certificado de quinta categoría con logging integrado.
    
    Args:
        ruta_pdf: Ruta completa del archivo PDF
        logger: Objeto logger opcional para registro de eventos
        
    Returns:
        Diccionario con: nombre, dni, tipo_doc, exito, observaciones
    """
    
    # Validar existencia del archivo
    if not Path(ruta_pdf).exists():
        resultado = {
            "nombre": None,
            "dni": None,
            "tipo_doc": "QUINTA",
            "exito": False,
            "observaciones": "Archivo no encontrado"
        }
        if logger:
            logger.error(f"❌ QUINTA - Archivo no encontrado: {ruta_pdf}")
        return resultado
    
    # Inicio de procesamiento con logging
    nombre_archivo = Path(ruta_pdf).name
    if logger:
        logger.debug(f"🔍 QUINTA - Iniciando procesamiento: {nombre_archivo}")
    
    resultado = {
        "nombre": None,
        "dni": None,
        "tipo_doc": "QUINTA",
        "exito": False,
        "observaciones": ""
    }
    
    try:
        # Leer primera página del PDF
        with pdfplumber.open(ruta_pdf) as pdf:
            if not pdf.pages:
                resultado["observaciones"] = "PDF sin páginas"
                if logger:
                    logger.warning(f"⚠️ QUINTA - PDF sin páginas: {nombre_archivo}")
                return resultado
            
            primera_pagina = pdf.pages[0]
            texto = primera_pagina.extract_text()
            
            if not texto or not texto.strip():
                resultado["observaciones"] = "Primera página sin texto extraíble"
                if logger:
                    logger.warning(f"⚠️ QUINTA - Primera página sin texto extraíble: {nombre_archivo}")
                return resultado
        
        # Corrección de encoding (caracteres UTF-8 mal interpretados)
        correcciones_encoding = {
            "CategorÃ­a": "Categoría",
            "Quinta CategorÃ­a": "Quinta Categoría",
            "QUINTA CATEGORÃ\x8dA": "QUINTA CATEGORÍA",
            "SRÃ\x81": "SRÁ",
            "SRÃ\x8dA": "SRÍA",
            "Ã\xad": "í",  # í
            "Ã³": "ó",     # ó
            "Ãº": "ú",     # ú
            "Ã©": "é",     # é
            "Ã¡": "á",     # á
            "Ã±": "ñ",     # ñ
            "Ã‰": "É",     # É
            "Ã“": "Ó",     # Ó
            "Ã": "Í",      # Í
            "Ã\x81": "Á",  # Á
            "Ã\x8d": "Í",  # Í
        }
        
        for mal, bien in correcciones_encoding.items():
            texto = texto.replace(mal, bien)
        
        # Patrón para el Nombre (mejorado para más robustez)
        patrones_nombre = [
            r"SR\(A\):\s*(.+?),\s*CON DNI",  # Patrón original
            r"SEÑOR\(A\):\s*(.+?),\s*CON DNI",  # Variante con SEÑOR
            r"SR\.?\s*(.+?),\s*CON DNI",  # Variante con punto
            r"NOMBRE:\s*(.+?)\s*(?:,|CON DNI|$)",  # Variante con NOMBRE:
        ]
        
        nombre_encontrado = None
        for i, patron in enumerate(patrones_nombre):
            match_nombre = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
            if match_nombre:
                nombre_raw = match_nombre.group(1).strip()
                
                # Aplicar correcciones de encoding al nombre
                for mal, bien in correcciones_encoding.items():
                    nombre_raw = nombre_raw.replace(mal, bien)
                
                # Limpieza adicional del nombre
                nombre_raw = re.sub(r'\s+', ' ', nombre_raw)  # Espacios múltiples a uno
                nombre_raw = nombre_raw.strip()
                
                nombre_encontrado = nombre_raw
                resultado["nombre"] = nombre_encontrado
                
                if logger:
                    logger.debug(f"🔍 QUINTA - Nombre encontrado (patrón {i+1}): {nombre_encontrado}")
                break
        
        # Patrón para el DNI (mejorado)
        patrones_dni = [
            r"CON DNI\s*[:\.]?\s*(\d{8,})",  # Original mejorado
            r"DNI\s*[:\.]?\s*(\d{8,})",  # Variante sin CON
            r"DOCUMENTO.*?(\d{8,})",  # Variante con DOCUMENTO
            r"C\.I\.\s*[:\.]?\s*(\d{8,})",  # Variante con C.I.
        ]
        
        dni_encontrado = None
        for i, patron in enumerate(patrones_dni):
            match_dni = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
            if match_dni:
                dni_raw = match_dni.group(1).strip()
                # Tomar solo los primeros 8 dígitos si hay más
                dni_encontrado = dni_raw[:8] if len(dni_raw) > 8 else dni_raw
                resultado["dni"] = dni_encontrado
                
                if logger:
                    logger.debug(f"🔍 QUINTA - DNI encontrado (patrón {i+1}): {dni_encontrado}")
                break
        
        # Determinar éxito y observaciones usando función auxiliar
        exito, observaciones = _determinar_resultado(
            resultado["nombre"], 
            resultado["dni"],
            logger
        )
        resultado["exito"] = exito
        resultado["observaciones"] = observaciones
        
        # Log final de resultado
        if logger:
            if exito:
                logger.info(f"✅ QUINTA - Extracción exitosa: {resultado['nombre']} | DNI: {resultado['dni']}")
            else:
                logger.warning(f"⚠️ QUINTA - Extracción fallida: {observaciones}")
        
        return resultado
        
    except FileNotFoundError as e:
        resultado["observaciones"] = f"Archivo no encontrado: {str(e)}"
        if logger:
            logger.error(f"❌ QUINTA - FileNotFoundError: {str(e)}")
        return resultado
        
    except IndexError as e:
        resultado["observaciones"] = f"Error al acceder a páginas PDF: {str(e)}"
        if logger:
            logger.error(f"❌ QUINTA - IndexError: {str(e)}")
        return resultado
        
    except pdfplumber.exceptions.PDFSyntaxError as e:
        resultado["observaciones"] = f"Error de sintaxis en PDF: {str(e)}"
        if logger:
            logger.error(f"❌ QUINTA - PDFSyntaxError: {str(e)}")
        return resultado
        
    except Exception as e:
        resultado["observaciones"] = f"Error inesperado al procesar PDF: {str(e)}"
        if logger:
            logger.error(f"❌ QUINTA - Error inesperado: {str(e)}")
        return resultado