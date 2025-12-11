#!/usr/bin/env python3
"""
Script para dividir PDFs en páginas individuales según palabras clave en nombres de archivos.
Autor: Cirujano de Código
Descripción: Clasifica y divide PDFs de carpeta madre en subcarpetas específicas.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter

# Importar logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger

# Inicializar logger
logger = Logger("CorePipeline2_Mover")

# Configuración de palabras clave
PALABRAS_CLAVE = {
    "1_Boletas": ["boleta", "boletas"],
    "2_Afp": ["afp"],
    "3_5ta": ["quinta"],
    "4_Convocatoria": ["convocatoria", "convocatorias"],
    "5_CertificadosTrabajo": ["certificado de trabajo", "certificados de trabajo"]
}

# Nombres base para archivos resultantes
NOMBRES_BASE = {
    "1_Boletas": "boleta",
    "2_Afp": "afp", 
    "3_5ta": "quinta",
    "4_Convocatoria": "convocatoria",
    "5_CertificadosTrabajo": "certif_trabajo"
}

def verificar_archivos_en_carpetas(carpetas):
    """
    Verifica si las carpetas destino contienen archivos.
    
    Args:
        carpetas (list): Lista de rutas de carpetas a verificar.
    
    Returns:
        dict: Diccionario con carpetas que contienen archivos y su cantidad.
    """
    carpetas_con_archivos = {}
    
    for carpeta in carpetas:
        if os.path.exists(carpeta):
            archivos = [f for f in os.listdir(carpeta) 
                       if os.path.isfile(os.path.join(carpeta, f))]
            if archivos:
                carpetas_con_archivos[carpeta] = len(archivos)
    
    return carpetas_con_archivos

def preguntar_sobrescribir_cli(carpetas_con_archivos):
    """
    Pregunta al usuario si desea sobrescribir archivos existentes (solo para CLI).
    El worker maneja esto desde la UI directamente.
    
    Args:
        carpetas_con_archivos (dict): Diccionario con carpetas que tienen archivos.
    
    Returns:
        bool: True si el usuario acepta sobrescribir, False si cancela.
    """
    if not carpetas_con_archivos:
        return True
    
    # Mostrar en consola
    logger.warning("="*60)
    logger.warning("ADVERTENCIA: Carpetas con archivos existentes")
    logger.warning("="*60)
    
    print("\n" + "="*60)
    print("ADVERTENCIA: Carpetas con archivos existentes")
    print("="*60)
    for carpeta, cantidad in carpetas_con_archivos.items():
        nombre_carpeta = os.path.basename(carpeta)
        logger.warning(f"  {nombre_carpeta}: {cantidad} archivo(s)")
        print(f"  {nombre_carpeta}: {cantidad} archivo(s)")
    print("="*60)
    
    # Preguntar en consola
    respuesta_consola = input("\n¿Continuar y sobrescribir? (s/n): ").lower()
    
    if respuesta_consola not in ['s', 'si', 'sí', 'y', 'yes']:
        return False
    
    # También mostrar diálogo gráfico
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Crear mensaje detallado
    mensaje = "Las siguientes carpetas destino contienen archivos:\n\n"
    for carpeta, cantidad in carpetas_con_archivos.items():
        nombre_carpeta = os.path.basename(carpeta)
        mensaje += f"• {nombre_carpeta}: {cantidad} archivo(s)\n"
    
    mensaje += "\n¿Desea continuar y sobrescribir los archivos existentes?"
    
    respuesta = messagebox.askyesno(
        "Advertencia - Archivos Existentes",
        mensaje
    )
    
    return respuesta

def buscar_pdfs_por_tipo(carpeta_madre):
    """
    Busca PDFs en la carpeta madre y los clasifica por tipo.
    
    Args:
        carpeta_madre (str): Ruta de la carpeta madre.
    
    Returns:
        dict: Diccionario con {tipo_carpeta: [lista_de_archivos]}.
        list: Archivos no clasificados.
    """
    pdfs_por_tipo = {tipo: [] for tipo in PALABRAS_CLAVE.keys()}
    pdfs_no_clasificados = []
    
    if not os.path.exists(carpeta_madre):
        logger.error(f"Carpeta madre no existe: {carpeta_madre}")
        return pdfs_por_tipo, pdfs_no_clasificados
    
    # Buscar todos los archivos PDF
    archivos_pdf = [f for f in os.listdir(carpeta_madre) 
                   if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(carpeta_madre, f))]
    
    logger.info(f"Encontrados {len(archivos_pdf)} archivo(s) PDF en carpeta madre")
    
    for archivo in archivos_pdf:
        nombre_lower = archivo.lower()
        asignado = False
        
        for tipo, palabras in PALABRAS_CLAVE.items():
            for palabra in palabras:
                if palabra in nombre_lower:
                    pdfs_por_tipo[tipo].append(archivo)
                    logger.info(f"Clasificado: '{archivo}' → {tipo} (palabra: '{palabra}')")
                    asignado = True
                    break
            if asignado:
                break
        
        if not asignado:
            pdfs_no_clasificados.append(archivo)
            logger.info(f"No clasificado: '{archivo}' - No coincide con palabras clave")
    
    return pdfs_por_tipo, pdfs_no_clasificados

def validar_unico_archivo_por_tipo(pdfs_por_tipo):
    """
    Valida que haya solo un archivo PDF por cada tipo.
    
    Args:
        pdfs_por_tipo (dict): Diccionario con PDFs clasificados por tipo.
    
    Returns:
        bool: True si hay máximo 1 archivo por tipo, False si hay múltiples.
    """
    tipos_problematicos = []
    
    for tipo, archivos in pdfs_por_tipo.items():
        if len(archivos) > 1:
            tipos_problematicos.append((tipo, archivos))
            logger.warning(f"Múltiples archivos para {tipo}: {len(archivos)} encontrados")
    
    if tipos_problematicos:
        # Loggear detalles del error
        logger.error("="*60)
        logger.error("ERROR: Múltiples archivos encontrados")
        logger.error("="*60)
        
        for tipo, archivos in tipos_problematicos:
            logger.error(f"\n{tipo}:")
            for archivo in archivos:
                logger.error(f"  • {archivo}")
        
        logger.error("="*60)
        
        return False
    
    return True

def limpiar_carpeta_destino(carpeta):
    """
    Elimina todos los archivos de una carpeta destino.
    
    Args:
        carpeta (str): Ruta de la carpeta a limpiar.
    """
    if not os.path.exists(carpeta):
        return
    
    archivos = [f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f))]
    
    for archivo in archivos:
        try:
            ruta_archivo = os.path.join(carpeta, archivo)
            os.remove(ruta_archivo)
            logger.info(f"    Eliminado: {archivo}")
        except Exception as e:
            logger.error(f"    Error al eliminar '{archivo}': {e}")

def dividir_pdf(ruta_pdf, carpeta_destino, nombre_base):
    """
    Divide un PDF en páginas individuales.
    
    Args:
        ruta_pdf (str): Ruta del PDF a dividir.
        carpeta_destino (str): Carpeta donde se guardarán las páginas.
        nombre_base (str): Nombre base para los archivos resultantes.
    
    Returns:
        tuple: (exito: bool, paginas: int, mensaje_error: str o None)
    """
    try:
        # Crear carpeta destino si no existe
        os.makedirs(carpeta_destino, exist_ok=True)
        
        # Abrir el PDF
        with open(ruta_pdf, 'rb') as archivo:
            lector = PdfReader(archivo)
            total_paginas = len(lector.pages)
            
            logger.info(f"  Procesando {total_paginas} página(s)...")
            
            # Dividir cada página
            for i, pagina in enumerate(lector.pages, start=1):
                escritor = PdfWriter()
                escritor.add_page(pagina)
                
                # Nombre del archivo resultante
                nombre_salida = f"{nombre_base}_{i}.pdf"
                ruta_salida = os.path.join(carpeta_destino, nombre_salida)
                
                # Guardar página
                with open(ruta_salida, 'wb') as archivo_salida:
                    escritor.write(archivo_salida)
                
                logger.info(f"    ✓ Generado: {nombre_salida}")
            
            logger.info(f"  ✓ Completado: {total_paginas} páginas generadas")
            return True, total_paginas, None
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"  ✗ Error al procesar PDF: {error_msg}")
        return False, 0, error_msg

def procesar_pdfs(carpeta_madre, sobrescribir=True):
    """
    Procesa todos los PDFs de la carpeta madre.
    
    Args:
        carpeta_madre (str): Ruta de la carpeta madre.
        sobrescribir (bool): Si True, sobrescribe archivos existentes.
    
    Returns:
        dict: Resumen del procesamiento.
    """
    # 1. Buscar y clasificar PDFs
    logger.info("Buscando PDFs...")
    pdfs_por_tipo, pdfs_no_clasificados = buscar_pdfs_por_tipo(carpeta_madre)
    
    total_clasificados = sum(len(archivos) for archivos in pdfs_por_tipo.values())
    
    if total_clasificados == 0:
        error_msg = "No se encontraron PDFs clasificables en la carpeta"
        logger.error(error_msg)
        return {"error": error_msg}
    
    logger.info(f"Total PDFs clasificados: {total_clasificados}")
    if pdfs_no_clasificados:
        logger.info(f"PDFs no clasificados: {len(pdfs_no_clasificados)}")
    
    # 2. Validar un solo archivo por tipo
    logger.info("Validando archivos únicos...")
    if not validar_unico_archivo_por_tipo(pdfs_por_tipo):
        return {"error": "Se encontraron múltiples archivos para un mismo tipo"}
    
    # 3. Verificar carpetas destino
    carpetas_destino = [os.path.join(carpeta_madre, tipo) for tipo in PALABRAS_CLAVE.keys()]
    carpetas_con_archivos = verificar_archivos_en_carpetas(carpetas_destino)
    
    if carpetas_con_archivos and not sobrescribir:
        return {"cancelado": "Usuario no aceptó sobrescribir"}
    
    # 4. Limpiar carpetas destino si se aceptó sobrescribir
    if sobrescribir:
        logger.info("Limpiando carpetas destino...")
        for carpeta in carpetas_destino:
            limpiar_carpeta_destino(carpeta)
    
    # 5. Procesar cada tipo de PDF
    logger.info("\nProcesando PDFs...")
    resumen = {
        "total_paginas": 0,
        "pdfs_procesados": 0,
        "pdfs_con_error": 0,
        "errores": [],
        "detalle_por_tipo": {}
    }
    
    for tipo, archivos in pdfs_por_tipo.items():
        if not archivos:  # No hay archivos de este tipo
            resumen["detalle_por_tipo"][tipo] = {"procesado": False, "mensaje": "No hay archivos"}
            continue
        
        archivo = archivos[0]  # Solo hay uno (validado anteriormente)
        ruta_pdf = os.path.join(carpeta_madre, archivo)
        carpeta_destino = os.path.join(carpeta_madre, tipo)
        nombre_base = NOMBRES_BASE[tipo]
        
        logger.info(f"\nProcesando {tipo}: {archivo}")
        
        # Dividir PDF
        exito, paginas, mensaje_error = dividir_pdf(ruta_pdf, carpeta_destino, nombre_base)
        
        if exito:
            resumen["total_paginas"] += paginas
            resumen["pdfs_procesados"] += 1
            resumen["detalle_por_tipo"][tipo] = {
                "procesado": True,
                "archivo": archivo,
                "paginas": paginas
            }
        else:
            resumen["pdfs_con_error"] += 1
            resumen["errores"].append({
                "tipo": tipo,
                "archivo": archivo,
                "error": mensaje_error
            })
            resumen["detalle_por_tipo"][tipo] = {
                "procesado": False,
                "archivo": archivo,
                "error": mensaje_error
            }
            logger.error(f"  ✗ Error procesando {archivo}: {mensaje_error}")
    
    # 6. Registrar PDFs no clasificados
    resumen["pdfs_no_clasificados"] = len(pdfs_no_clasificados)
    if pdfs_no_clasificados:
        logger.info(f"\nPDFs no clasificados (mantenidos en carpeta madre):")
        for archivo in pdfs_no_clasificados:
            logger.info(f"  • {archivo}")
    
    return resumen

def mostrar_resumen_final(resumen, carpeta_madre):
    """
    Muestra un resumen final del procesamiento.
    
    Args:
        resumen (dict): Resumen del procesamiento.
        carpeta_madre (str): Ruta de la carpeta madre.
    """
    logger.info("="*60)
    logger.info("RESUMEN DEL PROCESAMIENTO")
    logger.info("="*60)
    
    print("\n" + "="*60)
    print("RESUMEN DEL PROCESAMIENTO")
    print("="*60)
    
    if "error" in resumen:
        logger.error(f"ERROR: {resumen['error']}")
        print(f"ERROR: {resumen['error']}")
        return
    
    if "cancelado" in resumen:
        logger.warning("PROCESAMIENTO CANCELADO")
        print("PROCESAMIENTO CANCELADO")
        return
    
    logger.info(f"PDFs procesados exitosamente: {resumen['pdfs_procesados']}")
    logger.info(f"PDFs con errores: {resumen['pdfs_con_error']}")
    logger.info(f"Total de páginas generadas: {resumen['total_paginas']}")
    logger.info(f"PDFs no clasificados: {resumen.get('pdfs_no_clasificados', 0)}")
    
    print(f"PDFs procesados exitosamente: {resumen['pdfs_procesados']}")
    print(f"PDFs con errores: {resumen['pdfs_con_error']}")
    print(f"Total de páginas generadas: {resumen['total_paginas']}")
    print(f"PDFs no clasificados: {resumen.get('pdfs_no_clasificados', 0)}")
    
    print("\nDetalle por tipo:")
    logger.info("Detalle por tipo:")
    for tipo, detalle in resumen.get("detalle_por_tipo", {}).items():
        nombre_base = NOMBRES_BASE.get(tipo, tipo)
        if detalle.get("procesado"):
            msg = f"  • {nombre_base.upper()}: {detalle['archivo']} → {detalle['paginas']} páginas"
            logger.info(msg)
            print(msg)
        else:
            if "error" in detalle:
                msg = f"  • {nombre_base.upper()}: ERROR - {detalle['error']}"
                logger.error(msg)
                print(msg)
            else:
                msg = f"  • {nombre_base.upper()}: No procesado"
                logger.warning(msg)
                print(msg)
    
    if resumen.get("errores"):
        print("\nErrores encontrados:")
        logger.error("Errores encontrados:")
        for error in resumen["errores"]:
            msg = f"  • {error['tipo']} - {error['archivo']}: {error['error']}"
            logger.error(msg)
            print(msg)
    
    print("="*60)
    logger.info("="*60)
    
    # Mostrar mensaje gráfico
    if resumen["pdfs_procesados"] > 0:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        mensaje = f"Procesamiento completado:\n\n"
        mensaje += f"• PDFs procesados: {resumen['pdfs_procesados']}\n"
        mensaje += f"• Páginas generadas: {resumen['total_paginas']}\n"
        mensaje += f"• PDFs con errores: {resumen['pdfs_con_error']}\n"
        
        messagebox.showinfo("Procesamiento Completado", mensaje)

def main():
    """
    Función principal del script.
    """
    logger.info("="*60)
    logger.info("DIVISOR DE PDFs POR PALABRAS CLAVE")
    logger.info("="*60)
    
    print("="*60)
    print("DIVISOR DE PDFs POR PALABRAS CLAVE")
    print("="*60)
    print("Este script dividirá PDFs en páginas individuales según:")
    print("  • 'boleta(s)' → Carpeta 1_Boletas (archivos: boleta_1.pdf, boleta_2.pdf, ...)")
    print("  • 'afp' → Carpeta 2_Afp (archivos: afp_1.pdf, afp_2.pdf, ...)")
    print("  • 'quinta' → Carpeta 3_5ta (archivos: quinta_1.pdf, quinta_2.pdf, ...)")
    print("  • 'convocatoria(s)' → Carpeta 4_Convocatoria (archivos: convocatoria_1.pdf, ...)")
    print("  • 'certificado de trabajo' → Carpeta 5_CertificadosTrabajo (archivos: certif_trabajo_1.pdf, ...)")
    print("="*60)
    
    # Seleccionar carpeta madre (usando tkinter o argumento)
    if len(sys.argv) > 1:
        carpeta_madre = sys.argv[1]
    else:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        carpeta_madre = tk.filedialog.askdirectory(
            title="Selecciona la carpeta madre con los PDFs"
        )
    
    if not carpeta_madre:
        logger.warning("Operación cancelada por el usuario")
        print("\nOperación cancelada por el usuario.")
        return
    
    logger.info(f"Carpeta madre seleccionada: {carpeta_madre}")
    print(f"\nCarpeta madre seleccionada: {carpeta_madre}")
    
    # Iniciar logging
    logger.info(f"🚀 Iniciando procesamiento en carpeta: {carpeta_madre}")
    
    # Verificar archivos en carpetas destino
    carpetas_destino = [os.path.join(carpeta_madre, tipo) for tipo in PALABRAS_CLAVE.keys()]
    carpetas_con_archivos = verificar_archivos_en_carpetas(carpetas_destino)
    
    # Preguntar si se desea sobrescribir
    sobrescribir = preguntar_sobrescribir_cli(carpetas_con_archivos)
    if not sobrescribir:
        logger.info("Procesamiento cancelado por el usuario (no sobrescribir)")
        print("\nProcesamiento cancelado por el usuario.")
        return
    
    # Confirmar procesamiento
    print(f"\nIniciando procesamiento en: {carpeta_madre}")
    respuesta = input("¿Continuar con el procesamiento? (s/n): ").lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        logger.info("Procesamiento cancelado por el usuario (confirmación)")
        print("Procesamiento cancelado.")
        return
    
    # Procesar PDFs
    resumen = procesar_pdfs(carpeta_madre, sobrescribir)
    
    # Mostrar resumen final (SIN log_filename)
    mostrar_resumen_final(resumen, carpeta_madre)
    
    logger.info("="*60)
    logger.info("PROCESAMIENTO FINALIZADO")
    logger.info("="*60)

if __name__ == "__main__":
    # Verificar dependencias
    try:
        from tkinter import filedialog
    except ImportError:
        print("ERROR: tkinter no está instalado.")
        print("En Ubuntu/Debian: sudo apt-get install python3-tk")
        print("En Windows/Mac: tkinter generalmente viene con Python")
        sys.exit(1)
    
    try:
        import PyPDF2
    except ImportError:
        print("ERROR: PyPDF2 no está instalado.")
        print("Instalar con: pip install PyPDF2")
        sys.exit(1)
    
    main()