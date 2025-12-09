"""
Extractor de datos para Certificados AFP
Extrae: nombre y DNI (opcional)
"""

import re
import pdfplumber
from typing import Dict, Optional


def extraer_datos_afp(ruta_pdf: str) -> Dict:
    """
    Extrae nombre y DNI de un certificado AFP.
    
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
        # Leer contenido del PDF
        texto = ""
        with pdfplumber.open(ruta_pdf) as pdf:
            for pagina in pdf.pages:
                extraido = pagina.extract_text()
                if extraido:
                    texto += extraido + "\n"
        
        if not texto.strip():
            resultado["observaciones"] = "PDF vacío o sin texto extraíble"
            return resultado
        
        # Patrón con DNI
        patron_con_dni = r"Que a don \(doña\)\s+([A-ZÁÉÍÓÚÑ\s]+),\s+CON\s+DNI\s+(\d{8})"
        match_dni = re.search(patron_con_dni, texto)
        
        if match_dni:
            resultado["nombre"] = match_dni.group(1).strip()
            resultado["dni"] = match_dni.group(2)
            resultado["exito"] = True
            resultado["observaciones"] = "OK"
            return resultado
        
        # Patrón sin DNI
        patron_sin_dni = r"Que a don \(doña\)\s+([A-ZÁÉÍÓÚÑ\s]+),"
        match_nombre = re.search(patron_sin_dni, texto)
        
        if match_nombre:
            resultado["nombre"] = match_nombre.group(1).strip()
            resultado["dni"] = None
            resultado["exito"] = True
            resultado["observaciones"] = "DNI no encontrado"
            return resultado
        
        # No se encontró ningún patrón
        resultado["observaciones"] = "No se encontró patrón de certificado AFP"
        return resultado
        
    except Exception as e:
        resultado["observaciones"] = f"Error al procesar PDF: {str(e)}"
        return resultado