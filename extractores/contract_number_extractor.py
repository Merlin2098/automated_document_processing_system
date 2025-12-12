"""
Extractor centralizado de números de contrato desde nombres de archivo.

Este módulo proporciona funciones para extraer, validar y normalizar
números de contrato de documentos procesados por DocFlow Eventuales.

Autor: Richi
Versión: 1.0
"""

import re
from typing import Optional
import os
import sys

# Agregar path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Subir al directorio raíz del proyecto
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.logger import Logger

logger = Logger("ContractNumberExtractor")


# ============================================================
# PATRONES DE EXTRACCIÓN
# ============================================================

# Patrones precompilados para mejor performance
PATTERN_STANDARD = re.compile(r'(\d{4,10})', re.IGNORECASE)
PATTERN_WITH_PREFIX = re.compile(r'(?:CONTRATO|CONTRACT|CT|C)[-_\s]*(\d{4,10})', re.IGNORECASE)
PATTERN_NUMERIC_ONLY = re.compile(r'^(\d{4,10})$')


# ============================================================
# FUNCIONES PRINCIPALES
# ============================================================

def extract_from_filename(filename: str) -> Optional[str]:
    """
    Extrae el número de contrato desde el nombre de un archivo.
    
    Prioriza patrones en este orden:
    1. Número con prefijo explícito (CONTRATO_12345, CT-67890)
    2. Secuencia numérica de 4-10 dígitos
    3. Primeros dígitos encontrados si no hay mejor match
    
    Args:
        filename: Nombre completo del archivo (con o sin extensión)
        
    Returns:
        Número de contrato extraído o None si no se encuentra
        
    Examples:
        >>> extract_from_filename("CONTRATO_12345_Boleta.pdf")
        '12345'
        >>> extract_from_filename("Documento_98765432_AFP.pdf")
        '98765432'
        >>> extract_from_filename("archivo_sin_numero.pdf")
        None
    """
    if not filename or not isinstance(filename, str):
        logger.warning(f"⚠️ Nombre de archivo inválido: {filename}")
        return None
    
    # Remover extensión para análisis
    nombre_base = os.path.splitext(filename)[0]
    
    # Estrategia 1: Buscar patrón con prefijo explícito
    match_prefix = PATTERN_WITH_PREFIX.search(nombre_base)
    if match_prefix:
        numero = match_prefix.group(1)
        if validate_contract_number(numero):
            logger.debug(f"✓ Extraído con prefijo: {numero} desde {filename}")
            return numero
    
    # Estrategia 2: Buscar secuencia numérica estándar
    match_standard = PATTERN_STANDARD.search(nombre_base)
    if match_standard:
        numero = match_standard.group(1)
        if validate_contract_number(numero):
            logger.debug(f"✓ Extraído estándar: {numero} desde {filename}")
            return numero
    
    # No se encontró número válido
    logger.warning(f"⚠️ No se pudo extraer contrato desde: {filename}")
    return None


def extract_from_pdf_content(pdf_path: str) -> Optional[str]:
    """
    Extrae número de contrato desde el contenido de un PDF (fallback).
    
    NOTA: Esta función requiere pdfplumber instalado y puede ser lenta.
    Se recomienda usar solo como fallback cuando extract_from_filename() falla.
    
    Args:
        pdf_path: Ruta completa al archivo PDF
        
    Returns:
        Número de contrato extraído o None si no se encuentra
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("⚠️ pdfplumber no está instalado. No se puede extraer desde contenido.")
        return None
    
    if not os.path.exists(pdf_path):
        logger.error(f"⚠️ Archivo no existe: {pdf_path}")
        return None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Buscar solo en primera página (optimización)
            if len(pdf.pages) > 0:
                texto = pdf.pages[0].extract_text()
                
                if texto:
                    # Aplicar mismos patrones que para filename
                    match_prefix = PATTERN_WITH_PREFIX.search(texto)
                    if match_prefix:
                        numero = match_prefix.group(1)
                        if validate_contract_number(numero):
                            logger.info(f"✓ Extraído desde PDF: {numero}")
                            return numero
                    
                    match_standard = PATTERN_STANDARD.search(texto)
                    if match_standard:
                        numero = match_standard.group(1)
                        if validate_contract_number(numero):
                            logger.info(f"✓ Extraído desde PDF: {numero}")
                            return numero
        
        logger.warning(f"⚠️ No se encontró contrato en contenido de: {os.path.basename(pdf_path)}")
        return None
        
    except Exception as e:
        logger.error(f"⚠️ Error extrayendo desde PDF {os.path.basename(pdf_path)}: {e}")
        return None


def validate_contract_number(number: str) -> bool:
    """
    Valida que un número de contrato tenga formato correcto.
    
    Criterios:
    - Solo dígitos
    - Longitud entre 4 y 10 caracteres
    - No puede ser solo ceros
    
    Args:
        number: Número de contrato a validar
        
    Returns:
        True si es válido, False en caso contrario
        
    Examples:
        >>> validate_contract_number("12345")
        True
        >>> validate_contract_number("123")
        False
        >>> validate_contract_number("0000")
        False
    """
    if not number or not isinstance(number, str):
        return False
    
    # Verificar que sea solo dígitos
    if not number.isdigit():
        return False
    
    # Verificar longitud
    if len(number) < 4 or len(number) > 10:
        return False
    
    # Rechazar números triviales (solo ceros)
    if number == '0' * len(number):
        return False
    
    return True


def normalize_contract_number(number: str) -> str:
    """
    Normaliza un número de contrato a formato estándar.
    
    Actualmente solo remueve espacios/guiones y convierte a string puro.
    Puede extenderse para padding con ceros, etc.
    
    Args:
        number: Número de contrato a normalizar
        
    Returns:
        Número normalizado
        
    Examples:
        >>> normalize_contract_number("12-345")
        '12345'
        >>> normalize_contract_number(" 67890 ")
        '67890'
    """
    if not number:
        return ""
    
    # Remover espacios, guiones, underscores
    normalizado = number.strip().replace('-', '').replace('_', '').replace(' ', '')
    
    return normalizado


def extract_and_validate(filename: str, pdf_path: Optional[str] = None) -> Optional[str]:
    """
    Función de conveniencia que extrae y valida en un solo paso.
    
    Intenta primero con filename, luego con contenido PDF si falla.
    
    Args:
        filename: Nombre del archivo
        pdf_path: (Opcional) Ruta completa al PDF para fallback
        
    Returns:
        Número de contrato validado y normalizado o None
    """
    # Intento 1: Desde filename
    numero = extract_from_filename(filename)
    
    if numero:
        return normalize_contract_number(numero)
    
    # Intento 2: Desde contenido PDF (fallback costoso)
    if pdf_path:
        logger.info(f"ℹ️ Fallback: Buscando en contenido de {os.path.basename(pdf_path)}")
        numero = extract_from_pdf_content(pdf_path)
        
        if numero:
            return normalize_contract_number(numero)
    
    return None


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def batch_extract(filenames: list[str]) -> dict[str, Optional[str]]:
    """
    Extrae números de contrato de múltiples archivos en batch.
    
    Args:
        filenames: Lista de nombres de archivo
        
    Returns:
        Diccionario {filename: contract_number}
    """
    resultados = {}
    
    for filename in filenames:
        numero = extract_from_filename(filename)
        resultados[filename] = numero
    
    return resultados


def get_extraction_stats(filenames: list[str]) -> dict:
    """
    Genera estadísticas de extracción sobre un conjunto de archivos.
    
    Args:
        filenames: Lista de nombres de archivo
        
    Returns:
        Diccionario con estadísticas:
        - total: Total de archivos procesados
        - exitosos: Archivos con contrato extraído
        - fallidos: Archivos sin contrato
        - tasa_exito: Porcentaje de éxito
    """
    resultados = batch_extract(filenames)
    
    total = len(resultados)
    exitosos = sum(1 for v in resultados.values() if v is not None)
    fallidos = total - exitosos
    tasa_exito = (exitosos / total * 100) if total > 0 else 0.0
    
    return {
        'total': total,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'tasa_exito': tasa_exito
    }


# ============================================================
# TESTING Y VALIDACIÓN
# ============================================================

if __name__ == "__main__":
    # Tests básicos
    test_cases = [
        "CONTRATO_12345_Boleta.pdf",
        "98765432_AFP_Certificado.pdf",
        "Documento_CT-456789_5ta.pdf",
        "archivo_sin_numero.pdf",
        "123_muy_corto.pdf",
        "12345678901_muy_largo.pdf",
        "0000_ceros.pdf"
    ]
    
    print("\n" + "="*60)
    print(" TEST: Contract Number Extractor")
    print("="*60)
    
    for filename in test_cases:
        numero = extract_from_filename(filename)
        status = "✓" if numero else "✗"
        print(f"{status} {filename:40} → {numero}")
    
    # Estadísticas
    stats = get_extraction_stats(test_cases)
    print("\n" + "="*60)
    print(" Estadísticas:")
    print(f"   Total: {stats['total']}")
    print(f"   Exitosos: {stats['exitosos']}")
    print(f"   Fallidos: {stats['fallidos']}")
    print(f"   Tasa de éxito: {stats['tasa_exito']:.1f}%")
    print("="*60)