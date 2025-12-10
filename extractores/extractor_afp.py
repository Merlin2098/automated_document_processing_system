"""
Extractor de datos para Certificados AFP
Extrae: nombre y DNI (opcional)
"""

import re
import pdfplumber
from pathlib import Path
from typing import Dict, Optional


def extraer_datos_afp(ruta_pdf: str, logger=None) -> Dict:
    """
    Extrae nombre y DNI de un certificado AFP con logging integrado.
    
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
            "tipo_doc": "AFP",
            "exito": False,
            "observaciones": "Archivo no encontrado"
        }
        if logger:
            logger.error(f"❌ AFP - Archivo no encontrado: {ruta_pdf}")
        return resultado
    
    # Inicio de procesamiento con logging
    nombre_archivo = Path(ruta_pdf).name
    if logger:
        logger.debug(f"🔍 AFP - Iniciando procesamiento: {nombre_archivo}")
    
    resultado = {
        "nombre": None,
        "dni": None,
        "tipo_doc": "AFP",
        "exito": False,
        "observaciones": ""
    }
    
    try:
        # Leer contenido del PDF
        texto = ""
        with pdfplumber.open(ruta_pdf) as pdf:
            for pagina in pdf.pages:
                extraido = pagina.extract_text()
                if extraido:
                    texto += extraido + "\n"
        
        if not texto.strip():
            resultado["observaciones"] = "PDF vacío o sin texto extraíble"
            if logger:
                logger.warning(f"⚠️ AFP - PDF vacío o sin texto extraíble: {nombre_archivo}")
            return resultado
        
        # Corrección de encoding (caracteres UTF-8 mal interpretados)
        correcciones_encoding = {
            "Ã\xad": "í",  # í
            "Ã³": "ó",     # ó
            "Ãº": "ú",     # ú
            "Ã©": "é",     # é
            "Ã¡": "á",     # á
            "Ã±": "ñ",     # ñ
            "Ã‰": "É",     # É
            "Ã“": "Ó",     # Ó
            "Ã": "Í",      # Í
        }
        
        for mal, bien in correcciones_encoding.items():
            texto = texto.replace(mal, bien)
        
        # Patrón con DNI
        patron_con_dni = r"Que a don \(doña\)\s+([A-ZÁÉÍÓÚÑ\s]+),\s+CON\s+DNI\s+(\d{8})"
        match_dni = re.search(patron_con_dni, texto)
        
        if match_dni:
            nombre = match_dni.group(1).strip()
            dni = match_dni.group(2)
            
            # Corrección adicional de encoding en nombre
            for mal, bien in correcciones_encoding.items():
                nombre = nombre.replace(mal, bien)
            
            resultado["nombre"] = nombre
            resultado["dni"] = dni
            resultado["exito"] = True
            resultado["observaciones"] = "OK"
            
            if logger:
                logger.info(f"✅ AFP - Extracción exitosa: {nombre} | DNI: {dni}")
            return resultado
        
        # Patrón sin DNI
        patron_sin_dni = r"Que a don \(doña\)\s+([A-ZÁÉÍÓÚÑ\s]+),"
        match_nombre = re.search(patron_sin_dni, texto)
        
        if match_nombre:
            nombre = match_nombre.group(1).strip()
            
            # Corrección adicional de encoding en nombre
            for mal, bien in correcciones_encoding.items():
                nombre = nombre.replace(mal, bien)
            
            resultado["nombre"] = nombre
            resultado["dni"] = None
            resultado["exito"] = True
            resultado["observaciones"] = "DNI no encontrado"
            
            if logger:
                logger.info(f"✅ AFP - Nombre extraído (sin DNI): {nombre}")
                logger.warning(f"⚠️ AFP - DNI no encontrado en: {nombre_archivo}")
            return resultado
        
        # No se encontró ningún patrón
        resultado["observaciones"] = "No se encontró patrón de certificado AFP"
        if logger:
            logger.warning(f"⚠️ AFP - No se encontró patrón de certificado: {nombre_archivo}")
        return resultado
        
    except FileNotFoundError as e:
        resultado["observaciones"] = f"Archivo no encontrado: {str(e)}"
        if logger:
            logger.error(f"❌ AFP - FileNotFoundError: {str(e)}")
        return resultado
        
    except pdfplumber.exceptions.PDFSyntaxError as e:
        resultado["observaciones"] = f"Error de sintaxis en PDF: {str(e)}"
        if logger:
            logger.error(f"❌ AFP - PDFSyntaxError: {str(e)}")
        return resultado
        
    except Exception as e:
        resultado["observaciones"] = f"Error inesperado al procesar PDF: {str(e)}"
        if logger:
            logger.error(f"❌ AFP - Error inesperado: {str(e)}")
        return resultado