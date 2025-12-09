"""
Script para procesar y fusionar documentos por contrato.
Pipeline: Escaneo → Copia → Diagnóstico → Fusión de PDFs por contrato

Desarrollado para Matrix File Processor v3.0
Autor: Richi
Versión: 1.0
"""

import os
import json
import shutil
import re
from datetime import datetime
from tkinter import Tk, filedialog
from typing import List, Dict, Tuple, Optional
try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("⚠ PyPDF2 no está instalado. Ejecuta: pip install PyPDF2")
    PdfMerger = None


# ============================================================
# MÓDULO 1: INTERFAZ Y SELECCIÓN
# ============================================================

def seleccionar_carpeta_madre() -> Optional[str]:
    """
    Abre explorador de archivos para seleccionar carpeta madre.
    
    Returns:
        str: Ruta de la carpeta madre o None si se cancela
    """
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    carpeta = filedialog.askdirectory(
        title="Selecciona la carpeta madre que contiene las 5 subcarpetas"
    )
    root.destroy()
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
# MÓDULO 2: ESCANEO Y COPIA INICIAL
# ============================================================

def escanear_pdfs_subcarpeta(ruta_subcarpeta: str) -> List[str]:
    """
    Escanea una subcarpeta y retorna solo archivos PDF (ignora JSONs).
    
    Args:
        ruta_subcarpeta: Ruta de la subcarpeta
        
    Returns:
        Lista de nombres de archivos PDF
    """
    try:
        archivos = os.listdir(ruta_subcarpeta)
        # Doble filtrado para seguridad: extensión .pdf Y no es .json
        pdfs = [
            f for f in archivos 
            if f.lower().endswith('.pdf') and not f.lower().endswith('.json')
        ]
        return pdfs
    except Exception as e:
        print(f"  ✗ Error al escanear subcarpeta: {e}")
        return []


def copiar_pdfs_a_procesamiento(carpeta_madre: str, subcarpetas: List[str], 
                                timestamp: str) -> Tuple[str, int, int]:
    """
    Copia todos los PDFs de las subcarpetas a carpeta Documentos_Procesar.
    
    Args:
        carpeta_madre: Ruta de la carpeta madre
        subcarpetas: Lista de subcarpetas a procesar
        timestamp: Timestamp único para el proceso
        
    Returns:
        Tupla (ruta_carpeta_procesar, archivos_copiados, errores)
    """
    # Crear carpeta Documentos_Procesar
    nombre_carpeta = f"Documentos_Procesar_{timestamp}"
    ruta_procesar = os.path.join(carpeta_madre, nombre_carpeta)
    
    try:
        os.makedirs(ruta_procesar, exist_ok=True)
        print(f"  ✓ Carpeta creada: {nombre_carpeta}")
    except Exception as e:
        print(f"  ✗ Error al crear carpeta: {e}")
        return "", 0, 0
    
    archivos_copiados = 0
    errores = 0
    
    # Copiar PDFs de cada subcarpeta
    for subcarpeta in subcarpetas:
        ruta_subcarpeta = os.path.join(carpeta_madre, subcarpeta)
        pdfs = escanear_pdfs_subcarpeta(ruta_subcarpeta)
        
        print(f"\n  Procesando: {subcarpeta}")
        print(f"  → PDFs encontrados: {len(pdfs)}")
        
        copiados_subcarpeta = 0
        for pdf in pdfs:
            origen = os.path.join(ruta_subcarpeta, pdf)
            destino = os.path.join(ruta_procesar, pdf)
            
            try:
                shutil.copy2(origen, destino)
                archivos_copiados += 1
                copiados_subcarpeta += 1
            except Exception as e:
                print(f"    ✗ Error copiando '{pdf}': {e}")
                errores += 1
        
        print(f"  ✓ Copiados: {copiados_subcarpeta}")
    
    return ruta_procesar, archivos_copiados, errores


# ============================================================
# MÓDULO 3: ANÁLISIS Y DIAGNÓSTICO
# ============================================================

def extraer_identificador_de_nombre(nombre_archivo: str) -> Optional[str]:
    """
    Extrae el número de contrato del nombre de archivo.
    Formato esperado: NUMERO_CATEGORIA.pdf
    
    Args:
        nombre_archivo: Nombre del archivo PDF
        
    Returns:
        Identificador (número de contrato) o None si no se puede extraer
    """
    # Usar regex para parsing robusto
    match = re.match(r'^(.+?)_(.+?)\.pdf$', nombre_archivo, re.IGNORECASE)
    if not match:
        return None
    
    parte_antes_guion = match.group(1)
    
    # Extraer solo el número de contrato (primeros dígitos)
    match_numero = re.match(r'^(\d+)', parte_antes_guion)
    if not match_numero:
        return None
    
    return match_numero.group(1)


def generar_diagnostico(ruta_procesar: str, timestamp: str) -> Dict:
    """
    Analiza carpeta Documentos_Procesar y genera diagnóstico de contratos.
    
    Args:
        ruta_procesar: Ruta de carpeta Documentos_Procesar
        timestamp: Timestamp del proceso
        
    Returns:
        Diccionario con estructura del diagnóstico
    """
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
        
        # Analizar cada PDF
        for pdf in pdfs:
            identificador = extraer_identificador_de_nombre(pdf)
            
            if identificador:
                # Inicializar contrato si no existe
                if identificador not in diagnostico['contratos']:
                    diagnostico['contratos'][identificador] = {
                        'archivos': [],
                        'cantidad_total': 0,
                        'nombre_pack': None
                    }
                
                # Agregar archivo al contrato
                diagnostico['contratos'][identificador]['archivos'].append(pdf)
                diagnostico['contratos'][identificador]['cantidad_total'] += 1
                diagnostico['total_archivos'] += 1
                
                # Si es boleta, usar como nombre del pack
                if 'BOLETA DE PAGO Y CERTIFICADOS' in pdf.upper():
                    # Extraer nombre sin extensión
                    nombre_base = os.path.splitext(pdf)[0]
                    diagnostico['contratos'][identificador]['nombre_pack'] = nombre_base
            else:
                print(f"  ⚠ Archivo sin identificador válido: {pdf}")
        
        diagnostico['total_contratos_unicos'] = len(diagnostico['contratos'])
        
    except Exception as e:
        print(f"  ✗ Error al generar diagnóstico: {e}")
    
    return diagnostico


def guardar_diagnostico(diagnostico: Dict, ruta_procesar: str, timestamp: str) -> str:
    """
    Guarda el diagnóstico en un archivo JSON dentro de Documentos_Procesar.
    
    Args:
        diagnostico: Diccionario con el diagnóstico
        ruta_procesar: Ruta de la carpeta Documentos_Procesar
        timestamp: Timestamp del proceso
        
    Returns:
        Ruta del archivo JSON creado
    """
    nombre_archivo = f"diagnostico_merge_{timestamp}.json"
    ruta_json = os.path.join(ruta_procesar, nombre_archivo)
    
    try:
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(diagnostico, f, indent=4, ensure_ascii=False)
        print(f"  ✓ Diagnóstico guardado: {nombre_archivo}")
        return ruta_json
    except Exception as e:
        print(f"  ✗ Error al guardar diagnóstico: {e}")
        return ""


# ============================================================
# MÓDULO 4: FUSIÓN DE PDFs POR CONTRATO
# ============================================================

def fusionar_pdfs_contrato(archivos: List[str], ruta_procesar: str, 
                          nombre_salida: str, ruta_destino: str) -> bool:
    """
    Fusiona múltiples PDFs en un solo archivo.
    
    Args:
        archivos: Lista de nombres de archivos PDF a fusionar
        ruta_procesar: Ruta donde están los PDFs origen
        nombre_salida: Nombre del archivo fusionado (sin extensión)
        ruta_destino: Carpeta donde guardar el PDF fusionado
        
    Returns:
        True si la fusión fue exitosa
    """
    if PdfMerger is None:
        print("  ✗ PyPDF2 no disponible. No se puede fusionar PDFs.")
        return False
    
    try:
        merger = PdfMerger()
        
        # Agregar cada PDF al merger
        for archivo in archivos:
            ruta_pdf = os.path.join(ruta_procesar, archivo)
            if os.path.exists(ruta_pdf):
                merger.append(ruta_pdf)
        
        # Guardar PDF fusionado
        ruta_salida = os.path.join(ruta_destino, f"{nombre_salida}.pdf")
        merger.write(ruta_salida)
        merger.close()
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error al fusionar PDFs: {e}")
        return False


def generar_packs_documentales(ruta_procesar: str, diagnostico: Dict, 
                               timestamp: str) -> Tuple[str, int, int]:
    """
    Genera PDFs fusionados por contrato en carpeta Documentos_Enviar.
    
    Args:
        ruta_procesar: Ruta de carpeta Documentos_Procesar
        diagnostico: Diccionario con diagnóstico
        timestamp: Timestamp del proceso
        
    Returns:
        Tupla (ruta_carpeta_enviar, packs_generados, errores)
    """
    # Crear carpeta Documentos_Enviar dentro de Documentos_Procesar
    nombre_carpeta = f"Documentos_Enviar_{timestamp}"
    ruta_enviar = os.path.join(ruta_procesar, nombre_carpeta)
    
    try:
        os.makedirs(ruta_enviar, exist_ok=True)
        print(f"  ✓ Carpeta creada: {nombre_carpeta}")
    except Exception as e:
        print(f"  ✗ Error al crear carpeta de envío: {e}")
        return "", 0, 0
    
    packs_generados = 0
    errores = 0
    
    # Generar pack por cada contrato
    for identificador, info in diagnostico['contratos'].items():
        # Usar nombre de boleta como nombre del pack, o identificador si no hay boleta
        nombre_pack = info['nombre_pack'] if info['nombre_pack'] else f"Pack_{identificador}"
        
        print(f"\n  Generando pack: {nombre_pack}")
        print(f"  → Fusionando {info['cantidad_total']} documento(s)")
        
        exito = fusionar_pdfs_contrato(
            info['archivos'],
            ruta_procesar,
            nombre_pack,
            ruta_enviar
        )
        
        if exito:
            packs_generados += 1
            print(f"  ✓ Pack generado exitosamente")
        else:
            errores += 1
    
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
    
    # Mostrar estadísticas de contratos
    if diagnostico['contratos']:
        cantidades = [info['cantidad_total'] for info in diagnostico['contratos'].values()]
        promedio = sum(cantidades) / len(cantidades)
        print(f"\n  Estadísticas de documentos por contrato:")
        print(f"    Promedio: {promedio:.1f} documentos")
        print(f"    Rango: {min(cantidades)} - {max(cantidades)} documentos")
    
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
    print(" Matrix File Processor v3.0")
    print("="*60)
    
    # Verificar PyPDF2
    if PdfMerger is None:
        print("\n✗ PyPDF2 no está instalado.")
        print("  Instálalo con: pip install PyPDF2")
        return
    
    # Generar timestamp único para todo el proceso
    timestamp = generar_timestamp()
    
    # PASO 1: Seleccionar carpeta madre
    print("\n[1/5] Seleccionando carpeta madre...")
    carpeta_madre = seleccionar_carpeta_madre()
    
    if not carpeta_madre:
        print("\n✗ No se seleccionó ninguna carpeta. Proceso cancelado.")
        return
    
    print(f"✓ Carpeta madre: {carpeta_madre}")
    
    # PASO 2: Validar y copiar PDFs
    print("\n[2/5] Validando estructura y copiando PDFs...")
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
    
    # PASO 3: Generar diagnóstico
    print("\n[3/5] Generando diagnóstico de criterios...")
    diagnostico = generar_diagnostico(ruta_procesar, timestamp)
    
    if diagnostico['total_contratos_unicos'] == 0:
        print("\n✗ No se encontraron contratos válidos.")
        return
    
    mostrar_resumen_diagnostico(diagnostico)
    guardar_diagnostico(diagnostico, ruta_procesar, timestamp)
    
    # PASO 4: Confirmar operación
    print("\n[4/5] Confirmación de operación...")
    if not confirmar_continuacion(diagnostico['total_contratos_unicos'], 
                                  diagnostico['total_archivos']):
        print("\n⚠ Operación cancelada por el usuario.")
        print(f"  Los archivos copiados permanecen en: {os.path.basename(ruta_procesar)}")
        return
    
    # PASO 5: Generar packs documentarios
    print("\n[5/5] Generando packs documentarios...")
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
        print(f"\n  📂 Estructura generada:")
        print(f"     {os.path.basename(ruta_procesar)}/")
        print(f"     ├── [PDFs originales copiados]")
        print(f"     ├── diagnostico_merge_{timestamp}.json")
        print(f"     └── {nombre_carpeta_enviar}/")
        print(f"         └── [Packs documentarios fusionados]\n")
    else:
        print("\n✗ El proceso finalizó con errores.")


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Proceso interrumpido por el usuario.")
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()