"""
Script para procesar y fusionar documentos por contrato.
Pipeline: Escaneo → Copia → Diagnóstico → Fusión de PDFs por contrato

Desarrollado para DocFlow Eventuales v3.0
Autor: Richi
Versión: 2.0 - OPTIMIZADO: Paralelización + Contract Extractor + Parquet
"""

import os
import json
import shutil
import re
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QApplication
from typing import List, Dict, Tuple, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import Logger

# Importar contract extractor centralizado
from extractores.contract_number_extractor import extract_from_filename, validate_contract_number

try:
    from PyPDF2 import PdfMerger, PdfReader
except ImportError:
    print("⚠ PyPDF2 no está instalado. Ejecuta: pip install PyPDF2")
    PdfMerger = None
    PdfReader = None

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    print("⚠ pandas/pyarrow no disponibles. Diagnóstico solo en JSON.")

logger = Logger("CorePipeline5_UnirFinal")

# Lock global para operaciones thread-safe
_counter_lock = Lock()


# ============================================================
# MÓDULO 0: ORDEN Y PRIORIDADES
# ============================================================

def definir_orden_documentos() -> Dict[str, int]:
    """
    Define el orden de prioridad para los tipos de documentos.
    
    Returns:
        Diccionario con patrones y sus prioridades (menor = primero)
    """
    return {
        'BOLETA DE PAGO Y CERTIFICADOS': 1,
        'AFP': 2,
        '5TA': 3,
        'CERTIFICADOS': 4,
        'CONVOCATORIA': 5
    }


def extraer_tipo_documento(nombre_archivo: str) -> str:
    """
    Extrae el tipo de documento basándose en el nombre del archivo.
    
    Args:
        nombre_archivo: Nombre del archivo PDF
        
    Returns:
        Tipo de documento identificado o 'DESCONOCIDO'
    """
    nombre_upper = nombre_archivo.upper()
    
    if 'BOLETA DE PAGO Y CERTIFICADOS' in nombre_upper or 'BOLETA' in nombre_upper:
        return 'BOLETA DE PAGO Y CERTIFICADOS'
    elif 'AFP' in nombre_upper:
        return 'AFP'
    elif '5TA' in nombre_upper or 'QUINTA' in nombre_upper:
        return '5TA'
    elif 'CONVOCATORIA' in nombre_upper:
        return 'CONVOCATORIA'
    elif 'CERTIFICADO' in nombre_upper:
        return 'CERTIFICADOS'
    else:
        return 'DESCONOCIDO'


def ordenar_archivos_por_tipo(archivos: List[str]) -> List[str]:
    """
    Ordena una lista de archivos según el tipo de documento.
    
    Args:
        archivos: Lista de nombres de archivos PDF
        
    Returns:
        Lista ordenada según prioridades definidas
    """
    orden_prioridades = definir_orden_documentos()
    
    def obtener_prioridad(archivo: str) -> Tuple[int, str]:
        """
        Obtiene la prioridad de un archivo para ordenamiento.
        
        Returns:
            Tupla (prioridad, nombre_archivo) para ordenamiento estable
        """
        tipo = extraer_tipo_documento(archivo)
        prioridad = orden_prioridades.get(tipo, 999)
        return (prioridad, archivo)
    
    archivos_ordenados = sorted(archivos, key=obtener_prioridad)
    
    logger.info("📋 Orden de documentos aplicado:")
    for idx, archivo in enumerate(archivos_ordenados, 1):
        tipo = extraer_tipo_documento(archivo)
        logger.info(f"   {idx}. {tipo}: {archivo}")
    
    return archivos_ordenados


# ============================================================
# MÓDULO 0.5: VALIDACIÓN LIGERA DE PDFs
# ============================================================

def validar_pdf_rapido(ruta_pdf: str) -> bool:
    """
    Validación RÁPIDA y mínima de PDF (solo header).
    No hace lectura profunda para mantener rendimiento.
    
    Args:
        ruta_pdf: Ruta completa al archivo PDF
        
    Returns:
        True si tiene header PDF válido
    """
    try:
        # Solo verificar que el archivo exista y tenga tamaño > 0
        if not os.path.exists(ruta_pdf) or os.path.getsize(ruta_pdf) == 0:
            return False
        
        # Verificación muy rápida de header (solo primeros 5 bytes)
        with open(ruta_pdf, 'rb') as f:
            header = f.read(5)
            return header == b'%PDF-'
    except:
        return False


# ============================================================
# MÓDULO 1: INTERFAZ Y SELECCIÓN
# ============================================================

def seleccionar_carpeta_madre() -> Optional[str]:
    """
    Abre explorador de archivos para seleccionar carpeta madre.
    
    Returns:
        str: Ruta de la carpeta madre o None si se cancela
    """
    logger.info("📂 Abriendo selector de carpeta madre...")
    
    # Verificar si ya existe una instancia de QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    carpeta = QFileDialog.getExistingDirectory(
        None,
        "Selecciona la carpeta madre que contiene las 5 subcarpetas",
        "",
        QFileDialog.Option.ShowDirsOnly
    )
    
    if carpeta:
        logger.info(f"✅ Carpeta seleccionada: {carpeta}")
    else:
        logger.warning("⚠️ Usuario canceló la selección")
    
    return carpeta if carpeta else None


def validar_y_detectar_subcarpetas(carpeta_madre: str) -> Tuple[List[str], List[str]]:
    """
    Valida la existencia de las 5 subcarpetas esperadas.
    
    Args:
        carpeta_madre: Ruta de la carpeta madre
        
    Returns:
        Tupla (carpetas_encontradas, carpetas_faltantes)
    """
    subcarpetas_esperadas = [
        '1_Boletas',
        '2_Afp',
        '3_5ta',
        '4_Convocatoria',
        '5_CertificadosTrabajo'
    ]
    
    encontradas = []
    faltantes = []
    
    for subcarpeta in subcarpetas_esperadas:
        ruta_completa = os.path.join(carpeta_madre, subcarpeta)
        if os.path.exists(ruta_completa) and os.path.isdir(ruta_completa):
            encontradas.append(subcarpeta)
        else:
            faltantes.append(subcarpeta)
    
    return encontradas, faltantes


def generar_timestamp() -> str:
    """
    Genera timestamp único para usar en todas las carpetas y archivos del proceso.
    
    Returns:
        Timestamp en formato DD.MM.YYYY_HH.MM.SS
    """
    return datetime.now().strftime("%d.%m.%Y_%H.%M.%S")


# ============================================================
# MÓDULO 2: ESCANEO Y COPIA PARALELIZADA (NUEVO)
# ============================================================

def escanear_pdfs_subcarpeta(ruta_subcarpeta: str) -> List[str]:
    """
    Escanea una subcarpeta y retorna archivos PDF.
    Solo hace validación mínima (extensión + archivo existe).
    
    Args:
        ruta_subcarpeta: Ruta de la subcarpeta
        
    Returns:
        Lista de nombres de archivos PDF válidos
    """
    try:
        archivos = os.listdir(ruta_subcarpeta)
        # Filtrar por extensión .pdf y excluir .json
        pdfs = [
            f for f in archivos 
            if f.lower().endswith('.pdf') and not f.lower().endswith('.json')
        ]
        return pdfs
        
    except Exception as e:
        logger.error(f"  ✗ Error al escanear subcarpeta: {e}")
        return []


def _copiar_subcarpeta_worker(carpeta_madre: str, subcarpeta: str, 
                              ruta_procesar: str) -> Tuple[str, int, int, List[str]]:
    """
    Worker thread para copiar PDFs de una subcarpeta específica.
    
    Args:
        carpeta_madre: Ruta de la carpeta madre
        subcarpeta: Nombre de la subcarpeta a procesar
        ruta_procesar: Carpeta destino
        
    Returns:
        Tupla (subcarpeta, copiados, errores, archivos_problematicos)
    """
    ruta_subcarpeta = os.path.join(carpeta_madre, subcarpeta)
    pdfs = escanear_pdfs_subcarpeta(ruta_subcarpeta)
    
    copiados = 0
    errores = 0
    problematicos = []
    
    logger.info(f"  [Thread] Procesando {subcarpeta}: {len(pdfs)} PDFs")
    
    for pdf in pdfs:
        origen = os.path.join(ruta_subcarpeta, pdf)
        destino = os.path.join(ruta_procesar, pdf)
        
        try:
            # Validación temprana opcional (puede comentarse para más velocidad)
            if not validar_pdf_rapido(origen):
                logger.warning(f"  ⚠ PDF potencialmente corrupto: {pdf}")
                problematicos.append(pdf)
                # Decidir si copiar de todas formas o skipear
                # Actualmente lo copiamos igual para no perder datos
            
            shutil.copy2(origen, destino)
            copiados += 1
            
        except Exception as e:
            logger.error(f"  ✗ Error copiando '{pdf}': {e}")
            errores += 1
    
    return subcarpeta, copiados, errores, problematicos


def copiar_pdfs_a_procesamiento(carpeta_madre: str, subcarpetas: List[str], 
                                timestamp: str) -> Tuple[str, int, int]:
    """
    Copia todos los PDFs de las subcarpetas a carpeta Documentos_Procesar.
    VERSIÓN PARALELIZADA con ThreadPoolExecutor.
    
    Args:
        carpeta_madre: Ruta de la carpeta madre
        subcarpetas: Lista de subcarpetas a procesar
        timestamp: Timestamp único para el proceso
        
    Returns:
        Tupla (ruta_carpeta_procesar, archivos_copiados, errores)
    """
    nombre_carpeta = f"Documentos_Procesar_{timestamp}"
    ruta_procesar = os.path.join(carpeta_madre, nombre_carpeta)
    
    try:
        os.makedirs(ruta_procesar, exist_ok=True)
        print(f"  ✓ Carpeta creada: {nombre_carpeta}")
        logger.info(f"  ✓ Carpeta creada: {nombre_carpeta}")
    except Exception as e:
        print(f"  ✗ Error al crear carpeta: {e}")
        logger.error(f"  ✗ Error al crear carpeta: {e}")
        return "", 0, 0
    
    archivos_copiados = 0
    errores = 0
    
    # Paralelizar con ThreadPoolExecutor (max_workers = número de subcarpetas)
    max_workers = min(len(subcarpetas), 5)
    
    print(f"\n  🚀 Copiando PDFs en paralelo ({max_workers} threads)...")
    logger.info(f"  🚀 Copiando PDFs en paralelo ({max_workers} threads)...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(_copiar_subcarpeta_worker, carpeta_madre, sc, ruta_procesar): sc
            for sc in subcarpetas
        }
        
        # Process as completed
        for future in as_completed(futures):
            subcarpeta = futures[future]
            try:
                sc_nombre, copiados, errs, problematicos = future.result()
                
                with _counter_lock:
                    archivos_copiados += copiados
                    errores += errs
                
                print(f"  ✓ {sc_nombre}: {copiados} archivos copiados")
                logger.info(f"  ✓ {sc_nombre}: {copiados} archivos copiados")
                
                if problematicos:
                    logger.warning(f"  ⚠ {sc_nombre}: {len(problematicos)} PDFs potencialmente problemáticos")
                
            except Exception as e:
                logger.error(f"  ✗ Error procesando {subcarpeta}: {e}")
                errores += 1
    
    return ruta_procesar, archivos_copiados, errores


# ============================================================
# MÓDULO 3: ANÁLISIS Y DIAGNÓSTICO (CON CONTRACT EXTRACTOR)
# ============================================================

def obtener_tamano_archivo_mb(ruta_archivo: str) -> float:
    """
    Obtiene el tamaño de un archivo en MB.
    
    Args:
        ruta_archivo: Ruta completa al archivo
        
    Returns:
        Tamaño en MB
    """
    try:
        tamano_bytes = os.path.getsize(ruta_archivo)
        return tamano_bytes / (1024 * 1024)
    except:
        return 0.0


def generar_diagnostico(ruta_procesar: str, timestamp: str) -> Dict:
    """
    Analiza carpeta Documentos_Procesar y genera diagnóstico de contratos.
    USA CONTRACT EXTRACTOR CENTRALIZADO.
    
    Args:
        ruta_procesar: Ruta de carpeta Documentos_Procesar
        timestamp: Timestamp del proceso
        
    Returns:
        Diccionario con estructura del diagnóstico
    """
    logger.info("📊 Generando diagnóstico de contratos...")
    
    diagnostico = {
        'timestamp': timestamp,
        'carpeta_procesamiento': os.path.basename(ruta_procesar),
        'total_contratos_unicos': 0,
        'total_archivos': 0,
        'contratos': {}
    }
    
    try:
        archivos = os.listdir(ruta_procesar)
        pdfs = [f for f in archivos if f.lower().endswith('.pdf')]
        
        for pdf in pdfs:
            # USA EL CONTRACT EXTRACTOR (centralizado)
            identificador = extract_from_filename(pdf)
            
            if identificador and validate_contract_number(identificador):
                if identificador not in diagnostico['contratos']:
                    diagnostico['contratos'][identificador] = {
                        'archivos': [],
                        'cantidad_total': 0,
                        'nombre_pack': None,
                        'tamano_total_mb': 0.0
                    }
                
                diagnostico['contratos'][identificador]['archivos'].append(pdf)
                diagnostico['contratos'][identificador]['cantidad_total'] += 1
                diagnostico['total_archivos'] += 1
                
                # Calcular tamaño
                ruta_completa = os.path.join(ruta_procesar, pdf)
                tamano = obtener_tamano_archivo_mb(ruta_completa)
                diagnostico['contratos'][identificador]['tamano_total_mb'] += tamano
                
                # Detectar nombre del pack desde boletas
                if 'BOLETA DE PAGO Y CERTIFICADOS' in pdf.upper():
                    nombre_base = os.path.splitext(pdf)[0]
                    diagnostico['contratos'][identificador]['nombre_pack'] = nombre_base
            else:
                logger.warning(f"  ⚠ Archivo sin identificador válido: {pdf}")
        
        diagnostico['total_contratos_unicos'] = len(diagnostico['contratos'])
        logger.info(f"✅ Diagnóstico generado: {diagnostico['total_contratos_unicos']} contratos únicos")
        
    except Exception as e:
        logger.error(f"  ✗ Error al generar diagnóstico: {e}")
    
    return diagnostico


def guardar_diagnostico(diagnostico: Dict, ruta_procesar: str, timestamp: str) -> str:
    """
    Guarda el diagnóstico en JSON (auditoría) y opcionalmente en Parquet (procesamiento).
    
    Args:
        diagnostico: Diccionario con el diagnóstico
        ruta_procesar: Ruta de la carpeta Documentos_Procesar
        timestamp: Timestamp del proceso
        
    Returns:
        Ruta del archivo JSON creado
    """
    # SIEMPRE guardar JSON para auditoría
    nombre_json = f"diagnostico_merge_{timestamp}.json"
    ruta_json = os.path.join(ruta_procesar, nombre_json)
    
    try:
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(diagnostico, f, indent=4, ensure_ascii=False)
        print(f"  ✓ Diagnóstico JSON guardado: {nombre_json}")
        logger.info(f"  ✓ Diagnóstico JSON guardado: {nombre_json}")
    except Exception as e:
        print(f"  ✗ Error al guardar diagnóstico JSON: {e}")
        logger.error(f"  ✗ Error al guardar diagnóstico JSON: {e}")
        return ""
    
    # Guardar en PARQUET si está disponible (para procesamiento eficiente)
    if PARQUET_AVAILABLE and diagnostico['contratos']:
        try:
            _guardar_diagnostico_parquet(diagnostico, ruta_procesar, timestamp)
        except Exception as e:
            logger.warning(f"  ⚠ No se pudo guardar en Parquet: {e}")
    
    return ruta_json


def _guardar_diagnostico_parquet(diagnostico: Dict, ruta_procesar: str, timestamp: str):
    """
    Guarda el diagnóstico en formato Parquet para procesamiento eficiente.
    
    Estructura:
    - contratos_metadata.parquet: tabla con info por contrato
    - archivos_detalle.parquet: tabla con info por archivo
    """
    # Tabla 1: Metadata de contratos
    contratos_data = []
    for numero_contrato, info in diagnostico['contratos'].items():
        contratos_data.append({
            'numero_contrato': numero_contrato,
            'cantidad_archivos': info['cantidad_total'],
            'tamano_total_mb': info['tamano_total_mb'],
            'nombre_pack': info['nombre_pack'] or f"Pack_{numero_contrato}"
        })
    
    df_contratos = pd.DataFrame(contratos_data)
    ruta_contratos = os.path.join(ruta_procesar, f"contratos_metadata_{timestamp}.parquet")
    df_contratos.to_parquet(ruta_contratos, engine='pyarrow', compression='snappy')
    logger.info(f"  ✓ Metadata contratos guardado: {os.path.basename(ruta_contratos)}")
    
    # Tabla 2: Detalle de archivos
    archivos_data = []
    for numero_contrato, info in diagnostico['contratos'].items():
        for archivo in info['archivos']:
            tipo_doc = extraer_tipo_documento(archivo)
            ruta_completa = os.path.join(ruta_procesar, archivo)
            tamano = obtener_tamano_archivo_mb(ruta_completa)
            
            archivos_data.append({
                'numero_contrato': numero_contrato,
                'filename': archivo,
                'tipo_documento': tipo_doc,
                'tamano_mb': tamano
            })
    
    df_archivos = pd.DataFrame(archivos_data)
    ruta_archivos = os.path.join(ruta_procesar, f"archivos_detalle_{timestamp}.parquet")
    df_archivos.to_parquet(ruta_archivos, engine='pyarrow', compression='snappy')
    logger.info(f"  ✓ Detalle archivos guardado: {os.path.basename(ruta_archivos)}")


# ============================================================
# MÓDULO 4: FUSIÓN DE PDFs POR CONTRATO
# ============================================================

def fusionar_pdfs_contrato(archivos: List[str], ruta_procesar: str, 
                          nombre_salida: str, ruta_destino: str,
                          max_size_mb: float = 100.0) -> bool:
    """
    Fusiona múltiples PDFs en un solo archivo con control de memoria.
    
    Args:
        archivos: Lista de nombres de archivos PDF a fusionar
        ruta_procesar: Ruta donde están los PDFs origen
        nombre_salida: Nombre del archivo fusionado (sin extensión)
        ruta_destino: Carpeta donde guardar el PDF fusionado
        max_size_mb: Tamaño máximo permitido en MB
        
    Returns:
        True si la fusión fue exitosa
    """
    if PdfMerger is None:
        logger.error("  ✗ PyPDF2 no disponible. No se puede fusionar PDFs.")
        return False
    
    try:
        # Ordenar archivos antes de fusionar
        archivos_ordenados = ordenar_archivos_por_tipo(archivos)
        
        # Calcular tamaño total
        tamano_total = sum(
            obtener_tamano_archivo_mb(os.path.join(ruta_procesar, f)) 
            for f in archivos_ordenados
        )
        
        # Si excede el límite, dividir en partes
        if tamano_total > max_size_mb:
            logger.warning(f"  ⚠ Pack excede {max_size_mb}MB ({tamano_total:.2f}MB), dividiendo...")
            return _fusionar_pdfs_en_partes(
                archivos_ordenados, ruta_procesar, nombre_salida, 
                ruta_destino, max_size_mb
            )
        
        # Fusión simple (todo en un archivo)
        merger = PdfMerger()
        
        for archivo in archivos_ordenados:
            ruta_pdf = os.path.join(ruta_procesar, archivo)
            try:
                merger.append(ruta_pdf)
            except Exception as e:
                logger.error(f"  ✗ Error agregando {archivo}: {e}")
                continue
        
        # Guardar resultado
        nombre_archivo_salida = f"{nombre_salida}.pdf"
        ruta_salida = os.path.join(ruta_destino, nombre_archivo_salida)
        
        merger.write(ruta_salida)
        merger.close()
        
        logger.info(f"  ✓ Pack fusionado: {nombre_archivo_salida} ({tamano_total:.2f}MB)")
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Error fusionando PDFs: {e}")
        return False


def _fusionar_pdfs_en_partes(archivos: List[str], ruta_procesar: str,
                            nombre_base: str, ruta_destino: str,
                            max_size_mb: float) -> bool:
    """
    Fusiona PDFs dividiendo en múltiples partes si excede el tamaño máximo.
    
    Args:
        archivos: Lista ordenada de archivos
        ruta_procesar: Ruta origen
        nombre_base: Nombre base del pack
        ruta_destino: Carpeta destino
        max_size_mb: Tamaño máximo por parte
        
    Returns:
        True si todas las partes se generaron exitosamente
    """
    parte_actual = 1
    archivos_parte_actual = []
    tamano_parte_actual = 0.0
    exito_total = True
    
    for archivo in archivos:
        ruta_completa = os.path.join(ruta_procesar, archivo)
        tamano = obtener_tamano_archivo_mb(ruta_completa)
        
        # Si agregar este archivo excede el límite, guardar parte actual
        if tamano_parte_actual + tamano > max_size_mb and archivos_parte_actual:
            nombre_parte = f"{nombre_base}_Parte{parte_actual}"
            exito = _guardar_parte_fusionada(
                archivos_parte_actual, ruta_procesar, nombre_parte, ruta_destino
            )
            
            if not exito:
                exito_total = False
            
            # Reiniciar para siguiente parte
            parte_actual += 1
            archivos_parte_actual = []
            tamano_parte_actual = 0.0
        
        archivos_parte_actual.append(archivo)
        tamano_parte_actual += tamano
    
    # Guardar última parte
    if archivos_parte_actual:
        nombre_parte = f"{nombre_base}_Parte{parte_actual}"
        exito = _guardar_parte_fusionada(
            archivos_parte_actual, ruta_procesar, nombre_parte, ruta_destino
        )
        
        if not exito:
            exito_total = False
    
    return exito_total


def _guardar_parte_fusionada(archivos: List[str], ruta_procesar: str,
                            nombre_salida: str, ruta_destino: str) -> bool:
    """
    Guarda una parte fusionada de PDFs.
    """
    try:
        merger = PdfMerger()
        
        for archivo in archivos:
            ruta_pdf = os.path.join(ruta_procesar, archivo)
            merger.append(ruta_pdf)
        
        nombre_archivo = f"{nombre_salida}.pdf"
        ruta_salida = os.path.join(ruta_destino, nombre_archivo)
        
        merger.write(ruta_salida)
        merger.close()
        
        logger.info(f"  ✓ Parte guardada: {nombre_archivo}")
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Error guardando parte: {e}")
        return False


def generar_packs_documentales(ruta_procesar: str, diagnostico: Dict, 
                               timestamp: str,
                               progress_callback: Optional[Callable] = None) -> Tuple[str, int, int]:
    """
    Genera los packs documentales fusionados por contrato.
    
    Args:
        ruta_procesar: Carpeta con PDFs a procesar
        diagnostico: Diccionario con diagnóstico de contratos
        timestamp: Timestamp del proceso
        progress_callback: Función opcional para reportar progreso (current, total)
        
    Returns:
        Tupla (ruta_carpeta_enviar, packs_generados, errores)
    """
    nombre_carpeta_enviar = f"Documentos_Enviar_{timestamp}"
    ruta_enviar = os.path.join(ruta_procesar, nombre_carpeta_enviar)
    
    try:
        os.makedirs(ruta_enviar, exist_ok=True)
        logger.info(f"  ✓ Carpeta creada: {nombre_carpeta_enviar}")
    except Exception as e:
        logger.error(f"  ✗ Error creando carpeta enviar: {e}")
        return "", 0, 0
    
    packs_generados = 0
    errores = 0
    total_contratos = diagnostico['total_contratos_unicos']
    
    for idx, (identificador, info) in enumerate(diagnostico['contratos'].items(), 1):
        nombre_pack = info['nombre_pack'] if info['nombre_pack'] else f"Pack_{identificador}"
        
        print(f"\n  Generando pack: {nombre_pack}")
        print(f"  → Fusionando {info['cantidad_total']} documento(s) ({info['tamano_total_mb']:.2f} MB)")
        
        if progress_callback:
            progress_callback(idx, total_contratos)
        
        exito = fusionar_pdfs_contrato(
            info['archivos'],
            ruta_procesar,
            nombre_pack,
            ruta_enviar,
            max_size_mb=100.0
        )
        
        if exito:
            packs_generados += 1
            print(f"  ✓ Pack generado exitosamente")
            logger.info(f"  ✓ Pack generado exitosamente")
        else:
            errores += 1
            logger.error(f"  ✗ Error generando pack")
    
    return ruta_enviar, packs_generados, errores


# ============================================================
# MÓDULO 5: REPORTES
# ============================================================

def mostrar_resumen_validacion(encontradas: List[str], faltantes: List[str]):
    """Muestra resumen de subcarpetas encontradas y faltantes."""
    print(f"\n{'='*60}")
    print(f" VALIDACIÓN DE ESTRUCTURA")
    print(f"{'='*60}")
    
    if encontradas:
        print(f"\n✓ Subcarpetas encontradas: {len(encontradas)}")
        for carpeta in encontradas:
            print(f"  • {carpeta}")
    
    if faltantes:
        print(f"\n⚠ Subcarpetas no encontradas: {len(faltantes)}")
        for carpeta in faltantes:
            print(f"  • {carpeta}")


def mostrar_resumen_diagnostico(diagnostico: Dict):
    """Muestra resumen del diagnóstico generado."""
    print(f"\n{'='*60}")
    print(f" DIAGNÓSTICO DE CRITERIOS DE UNIÓN")
    print(f"{'='*60}")
    print(f"  📊 Total de contratos únicos: {diagnostico['total_contratos_unicos']}")
    print(f"  📄 Total de archivos PDF: {diagnostico['total_archivos']}")
    
    if diagnostico['contratos']:
        cantidades = [info['cantidad_total'] for info in diagnostico['contratos'].values()]
        tamanos = [info['tamano_total_mb'] for info in diagnostico['contratos'].values()]
        promedio = sum(cantidades) / len(cantidades)
        tamano_promedio = sum(tamanos) / len(tamanos)
        
        print(f"\n  Estadísticas de documentos por contrato:")
        print(f"    Promedio: {promedio:.1f} documentos")
        print(f"    Rango: {min(cantidades)} - {max(cantidades)} documentos")
        print(f"    Tamaño promedio: {tamano_promedio:.2f} MB")
    
    print(f"{'='*60}")


def confirmar_continuacion(total_contratos: int, total_archivos: int) -> bool:
    """
    Pide confirmación al usuario antes de proceder con la fusión.
    
    Args:
        total_contratos: Cantidad de contratos a procesar
        total_archivos: Cantidad total de archivos
        
    Returns:
        True si el usuario confirma, False en caso contrario
    """
    print(f"\n  ℹ️  Se generarán {total_contratos} packs documentarios fusionando {total_archivos} archivos")
    
    while True:
        respuesta = input("  ¿Continuar con la generación de packs? (s/n): ").strip().lower()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif respuesta in ['n', 'no']:
            return False
        else:
            print("  ✗ Respuesta inválida. Ingresa 's' o 'n'")


def mostrar_resumen_final(packs_generados: int, errores: int, 
                         nombre_carpeta_enviar: str):
    """Muestra resumen final de la operación."""
    print(f"\n{'='*60}")
    print(f" RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  ✓ Packs documentarios generados: {packs_generados}")
    
    if errores > 0:
        print(f"  ✗ Errores durante la fusión: {errores}")
    
    if packs_generados > 0:
        tasa_exito = (packs_generados / (packs_generados + errores)) * 100
        print(f"  📊 Tasa de éxito: {tasa_exito:.1f}%")
    
    print(f"\n  📁 Carpeta con packs: {nombre_carpeta_enviar}")
    print(f"{'='*60}")


# ============================================================
# MÓDULO 6: PROCESO PRINCIPAL
# ============================================================

def main():
    """Función principal que orquesta todo el proceso."""
    print("\n" + "="*60)
    print(" GENERADOR DE PACKS DOCUMENTARIOS")
    print(" DocFlow Eventuales v3.0")
    print("="*60)
    logger.info("="*60)
    logger.info(" GENERADOR DE PACKS DOCUMENTARIOS")
    logger.info(" DocFlow Eventuales v3.0")
    logger.info("="*60)
    
    if PdfMerger is None:
        print("\n✗ PyPDF2 no está instalado.")
        print("  Instálalo con: pip install PyPDF2")
        return
    
    timestamp = generar_timestamp()
    
    print("\n[1/5] Seleccionando carpeta madre...")
    logger.info("[1/5] Seleccionando carpeta madre...")
    carpeta_madre = seleccionar_carpeta_madre()
    
    if not carpeta_madre:
        print("\n✗ No se seleccionó ninguna carpeta. Proceso cancelado.")
        return
    
    print(f"✓ Carpeta madre: {carpeta_madre}")
    
    print("\n[2/5] Validando estructura y copiando PDFs...")
    logger.info("[2/5] Validando estructura y copiando PDFs...")
    encontradas, faltantes = validar_y_detectar_subcarpetas(carpeta_madre)
    
    if not encontradas:
        print("\n✗ No se encontró ninguna de las 5 subcarpetas esperadas.")
        return
    
    mostrar_resumen_validacion(encontradas, faltantes)
    
    if faltantes:
        print("\n  ⚠ ADVERTENCIA: Faltan algunas subcarpetas.")
        respuesta = input("  ¿Continuar solo con las encontradas? (s/n): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            print("\n⚠ Operación cancelada.")
            return
    
    print(f"\n  Copiando PDFs a carpeta de procesamiento...")
    print(f"{'='*60}")
    
    ruta_procesar, copiados, errores_copia = copiar_pdfs_a_procesamiento(
        carpeta_madre, encontradas, timestamp
    )
    
    if not ruta_procesar:
        print("\n✗ Error al crear carpeta de procesamiento.")
        return
    
    print(f"\n{'='*60}")
    print(f"  ✓ Total de PDFs copiados: {copiados}")
    if errores_copia > 0:
        print(f"  ✗ Errores durante la copia: {errores_copia}")
    print(f"{'='*60}")
    
    print("\n[3/5] Generando diagnóstico de criterios...")
    logger.info("[3/5] Generando diagnóstico de criterios...")
    diagnostico = generar_diagnostico(ruta_procesar, timestamp)
    
    if diagnostico['total_contratos_unicos'] == 0:
        print("\n✗ No se encontraron contratos válidos.")
        return
    
    mostrar_resumen_diagnostico(diagnostico)
    guardar_diagnostico(diagnostico, ruta_procesar, timestamp)
    
    print("\n[4/5] Confirmación de operación...")
    logger.info("[4/5] Confirmación de operación...")
    if not confirmar_continuacion(diagnostico['total_contratos_unicos'], 
                                  diagnostico['total_archivos']):
        print("\n⚠ Operación cancelada por el usuario.")
        print(f"  Los archivos copiados permanecen en: {os.path.basename(ruta_procesar)}")
        return
    
    print("\n[5/5] Generando packs documentarios...")
    logger.info("[5/5] Generando packs documentarios...")
    print(f"{'='*60}")
    
    ruta_enviar, packs, errores_fusion = generar_packs_documentales(
        ruta_procesar, diagnostico, timestamp
    )
    
    if ruta_enviar:
        nombre_carpeta_enviar = os.path.basename(ruta_enviar)
        mostrar_resumen_final(packs, errores_fusion, nombre_carpeta_enviar)
        
        print("\n" + "="*60)
        print(" PROCESO COMPLETADO EXITOSAMENTE")
        print("="*60)
        logger.info("="*60)
        logger.info(" PROCESO COMPLETADO EXITOSAMENTE")
        logger.info("="*60)
        print(f"\n  📂 Estructura generada:")
        print(f"     {os.path.basename(ruta_procesar)}/")
        print(f"     ├── [PDFs originales copiados]")
        print(f"     ├── diagnostico_merge_{timestamp}.json")
        if PARQUET_AVAILABLE:
            print(f"     ├── contratos_metadata_{timestamp}.parquet")
            print(f"     ├── archivos_detalle_{timestamp}.parquet")
        print(f"     └── {nombre_carpeta_enviar}/")
        print(f"         └── [Packs documentarios fusionados]\n")
    else:
        print("\n✗ El proceso finalizó con errores.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Proceso interrumpido por el usuario.")
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()