"""
Extractor de datos para Boletas de Pago
Extrae: nombre, DNI y fecha de ingreso
"""

import re
from pathlib import Path
from typing import Dict, Optional
from PyPDF2 import PdfReader


# Configuración de limpieza
LIMPIEZA_NOMBRE = ["FECHA ING", ",", ".", "\n", "\t"]


def limpiar_nombre(nombre: str) -> str:
    """Limpia el nombre de caracteres no deseados."""
    nombre_limpio = " ".join(nombre.split())
    for cadena in LIMPIEZA_NOMBRE:
        nombre_limpio = nombre_limpio.replace(cadena, "")
    return nombre_limpio.strip()


def _determinar_exito(nombre: Optional[str], dni: Optional[str], fecha: Optional[str]) -> tuple:
    """
    Determina el éxito de la extracción y genera observaciones.
    
    Args:
        nombre: Nombre extraído
        dni: DNI extraído
        fecha: Fecha extraída
        
    Returns:
        Tupla (exito: bool, observaciones: str)
    """
    if nombre and dni and fecha:
        return True, "OK"
    elif nombre and dni:
        return True, "Fecha de ingreso no encontrada"
    elif nombre:
        return False, "DNI no encontrado"
    else:
        return False, "No se encontró patrón de boleta de pago"


def extraer_datos_boleta(ruta_pdf: str, logger=None) -> Dict:
    """
    Extrae nombre, DNI y fecha de ingreso de una boleta de pago.
    
    Args:
        ruta_pdf: Ruta completa del archivo PDF
        logger: Logger opcional para registro de eventos
        
    Returns:
        Diccionario con: nombre, dni, fecha, tipo_doc, exito, observaciones
    """
    # Inicializar resultado base
    resultado = {
        "nombre": None,
        "dni": None,
        "fecha": None,
        "tipo_doc": "BOLETA",
        "exito": False,
        "observaciones": ""
    }
    
    # Validar existencia del archivo
    ruta_path = Path(ruta_pdf)
    if not ruta_path.exists():
        resultado["observaciones"] = "Archivo no encontrado"
        if logger:
            logger.error(f"❌ BOLETA - Archivo no encontrado: {ruta_pdf}")
        return resultado
    
    if logger:
        logger.debug(f"🔍 Procesando BOLETA: {ruta_path.name}")
    
    try:
        # Leer primera página del PDF
        with open(ruta_pdf, 'rb') as file:
            reader = PdfReader(file)
            
            if not reader.pages:
                resultado["observaciones"] = "PDF sin páginas"
                if logger:
                    logger.warning(f"⚠️ BOLETA - PDF sin páginas: {ruta_path.name}")
                return resultado
            
            texto = reader.pages[0].extract_text()
            
            if not texto.strip():
                resultado["observaciones"] = "Primera página sin texto extraíble"
                if logger:
                    logger.warning(f"⚠️ BOLETA - Sin texto extraíble: {ruta_path.name}")
                return resultado
        
        # Caracteres válidos para nombres
        CARACTERES_NOMBRE = r'[A-ZÑÁÉÍÓÚÜ\s\-\']'
        
        # Extraer DNI
        match_dni = re.search(r'CÓDIGO\s*(\d{8})', texto)
        if match_dni:
            resultado["dni"] = match_dni.group(1).strip()
        
        # Extraer Nombre (3 variantes)
        match_nombre = re.search(
            rf'APELLIDOS Y NOMBRES\s*({CARACTERES_NOMBRE}+)(?=\s*FECHA ING|\s*CÓDIGO CORP|\s*\d{{2,}}|\s*SUELDO)',
            texto,
            re.DOTALL
        )
        
        if not match_nombre:
            match_nombre = re.search(
                rf'({CARACTERES_NOMBRE}+)\s*FECHA ING\s*\d{{2}}/\d{{2}}/\d{{4}}',
                texto,
                re.DOTALL
            )
        
        if not match_nombre:
            match_nombre = re.search(
                rf'CÓDIGO CORP\s*APELLIDOS Y NOMBRES\s*({CARACTERES_NOMBRE}+)\s*ESSALUD',
                texto,
                re.DOTALL
            )
        
        if match_nombre:
            nombre_raw = match_nombre.group(1).strip()
            resultado["nombre"] = limpiar_nombre(nombre_raw)
        
        # Extraer Fecha de Ingreso
        match_fecha = re.search(r'FECHA ING\s*(\d{2}/\d{2}/\d{4})', texto)
        if match_fecha:
            fecha_raw = match_fecha.group(1).strip()
            resultado["fecha"] = fecha_raw.replace('/', '-')  # dd-mm-yyyy
        
        # Determinar éxito y observaciones
        exito, observaciones = _determinar_exito(
            resultado["nombre"],
            resultado["dni"],
            resultado["fecha"]
        )
        resultado["exito"] = exito
        resultado["observaciones"] = observaciones
        
        # Logging según resultado
        if logger:
            if exito and resultado["fecha"]:
                logger.info(
                    f"✅ BOLETA - Nombre: {resultado['nombre']}, "
                    f"DNI: {resultado['dni']}, Fecha: {resultado['fecha']}"
                )
            elif exito:
                logger.info(
                    f"✅ BOLETA - Nombre: {resultado['nombre']}, "
                    f"DNI: {resultado['dni']} (sin fecha)"
                )
            else:
                logger.warning(
                    f"⚠️ BOLETA - Extracción incompleta: {observaciones}"
                )
        
        return resultado
        
    except FileNotFoundError:
        resultado["observaciones"] = "Archivo no encontrado durante lectura"
        if logger:
            logger.error(f"❌ BOLETA - Archivo no encontrado: {ruta_pdf}")
        return resultado
        
    except Exception as e:
        resultado["observaciones"] = f"Error al procesar PDF: {str(e)}"
        if logger:
            logger.error(f"❌ BOLETA - Error: {str(e)} en {ruta_path.name}")
        return resultado