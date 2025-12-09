"""
Extractor de datos para Certificados de Quinta Categoría
Extrae: nombre y DNI
"""

import re
import pdfplumber
from typing import Dict


def extraer_datos_quinta(ruta_pdf: str) -> Dict:
    """
    Extrae nombre y DNI de un certificado de quinta categoría.
    
    Args:
        ruta_pdf: Ruta completa del archivo PDF
        
    Returns:
        Diccionario con: nombre, dni, exito, observaciones
    """
    resultado = {
        "nombre": None,
        "dni": None,
        "exito": False,
        "observaciones": ""
    }
    
    try:
        # Leer primera página del PDF
        with pdfplumber.open(ruta_pdf) as pdf:
            if not pdf.pages:
                resultado["observaciones"] = "PDF sin páginas"
                return resultado
            
            texto = pdf.pages[0].extract_text()
            
            if not texto or not texto.strip():
                resultado["observaciones"] = "Primera página sin texto extraíble"
                return resultado
        
        # Patrón para el Nombre
        patron_nombre = r"SR\(A\):\s*(.+?),\s*CON DNI"
        match_nombre = re.search(patron_nombre, texto, flags=re.IGNORECASE | re.DOTALL)
        
        if match_nombre:
            resultado["nombre"] = match_nombre.group(1).strip()
        
        # Patrón para el DNI
        patron_dni = r"CON DNI\s*(\d{8,})"
        match_dni = re.search(patron_dni, texto, flags=re.IGNORECASE | re.DOTALL)
        
        if match_dni:
            resultado["dni"] = match_dni.group(1).strip()
        
        # Determinar éxito y observaciones
        if resultado["nombre"] and resultado["dni"]:
            resultado["exito"] = True
            resultado["observaciones"] = "OK"
        elif resultado["nombre"]:
            resultado["exito"] = False
            resultado["observaciones"] = "DNI no encontrado"
        elif resultado["dni"]:
            resultado["exito"] = False
            resultado["observaciones"] = "Nombre no encontrado"
        else:
            resultado["exito"] = False
            resultado["observaciones"] = "No se encontró patrón de certificado de quinta"
        
        return resultado
        
    except Exception as e:
        resultado["observaciones"] = f"Error al procesar PDF: {str(e)}"
        return resultado