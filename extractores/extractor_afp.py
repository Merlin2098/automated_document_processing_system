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
        
        # Patrones con nombre + DNI (orden: nuevo formato primero, luego legacy)
        patrones_con_dni = [
            # Nuevo formato: "identificado(a) con DNI - 12345678"
            r"Que\s+a\s+don\s+\(doña\)\s+(?P<nombre>[A-ZÁÉÍÓÚÑ\s]+?)\s+identificado\(a\)\s+con\s+DNI\s*[-:.]?\s*(?P<dni>\d{8})",
            # Legacy: "NOMBRE, CON DNI 12345678"
            r"Que\s+a\s+don\s+\(doña\)\s+(?P<nombre>[A-ZÁÉÍÓÚÑ\s]+),\s*CON\s+DNI\s+(?P<dni>\d{8})",
        ]

        for i, patron in enumerate(patrones_con_dni):
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                nombre = match.group("nombre").strip()
                dni = match.group("dni")

                for mal, bien in correcciones_encoding.items():
                    nombre = nombre.replace(mal, bien)

                resultado["nombre"] = nombre
                resultado["dni"] = dni
                resultado["exito"] = True
                resultado["observaciones"] = "OK"

                if logger:
                    logger.info(f"✅ AFP - Extracción exitosa (patrón {i+1}): {nombre} | DNI: {dni}")
                return resultado

        # Fallback: extraer solo nombre (sin DNI) — se reporta como FALLO
        patrones_solo_nombre = [
            # Nuevo formato sin DNI: "NOMBRE identificado(a) con ..."
            r"Que\s+a\s+don\s+\(doña\)\s+(?P<nombre>[A-ZÁÉÍÓÚÑ\s]+?)\s+identificado\(a\)",
            # Legacy: "NOMBRE," (terminado en coma)
            r"Que\s+a\s+don\s+\(doña\)\s+(?P<nombre>[A-ZÁÉÍÓÚÑ\s]+),",
        ]

        # Detectar qué identificador se usó en lugar de DNI (para diagnóstico)
        match_id = re.search(r"identificado\(a\)\s+con\s+(?P<id_tipo>\w+)", texto, re.IGNORECASE)
        id_encontrado = match_id.group("id_tipo") if match_id else None

        for i, patron in enumerate(patrones_solo_nombre):
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                nombre = match.group("nombre").strip()

                for mal, bien in correcciones_encoding.items():
                    nombre = nombre.replace(mal, bien)

                obs = f"DNI no encontrado — identificador detectado: {id_encontrado}" if id_encontrado else "DNI no encontrado"
                resultado["nombre"] = nombre
                resultado["dni"] = None
                resultado["exito"] = False
                resultado["observaciones"] = obs

                if logger:
                    logger.error(f"❌ AFP - Sin DNI en: {nombre_archivo} | Nombre: {nombre} | Identificador: {id_encontrado or 'ninguno'}")
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