"""
Extractor de datos para Boletas de Pago
Extrae: nombre, DNI y fecha de ingreso
"""

import re
from PyPDF2 import PdfReader
from typing import Dict


# Configuración de limpieza
LIMPIEZA_NOMBRE = ["FECHA ING", ",", ".", "\n", "\t"]


def limpiar_nombre(nombre: str) -> str:
    """Limpia el nombre de caracteres no deseados."""
    nombre_limpio = " ".join(nombre.split())
    for cadena in LIMPIEZA_NOMBRE:
        nombre_limpio = nombre_limpio.replace(cadena, "")
    return nombre_limpio.strip()


def extraer_datos_boleta(ruta_pdf: str) -> Dict:
    """
    Extrae nombre, DNI y fecha de ingreso de una boleta de pago.
    
    Args:
        ruta_pdf: Ruta completa del archivo PDF
        
    Returns:
        Diccionario con: nombre, dni, fecha, exito, observaciones
    """
    resultado = {
        "nombre": None,
        "dni": None,
        "fecha": None,
        "exito": False,
        "observaciones": ""
    }
    
    try:
        # Leer primera página del PDF
        with open(ruta_pdf, 'rb') as file:
            reader = PdfReader(file)
            
            if not reader.pages:
                resultado["observaciones"] = "PDF sin páginas"
                return resultado
            
            texto = reader.pages[0].extract_text()
            
            if not texto.strip():
                resultado["observaciones"] = "Primera página sin texto extraíble"
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
        if resultado["nombre"] and resultado["dni"] and resultado["fecha"]:
            resultado["exito"] = True
            resultado["observaciones"] = "OK"
        elif resultado["nombre"] and resultado["dni"]:
            resultado["exito"] = True
            resultado["observaciones"] = "Fecha de ingreso no encontrada"
        elif resultado["nombre"]:
            resultado["exito"] = False
            resultado["observaciones"] = "DNI no encontrado"
        else:
            resultado["exito"] = False
            resultado["observaciones"] = "No se encontró patrón de boleta de pago"
        
        return resultado
        
    except Exception as e:
        resultado["observaciones"] = f"Error al procesar PDF: {str(e)}"
        return resultado