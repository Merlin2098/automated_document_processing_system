#!/usr/bin/env python3
"""
Script para dividir PDFs en páginas individuales según palabras clave en nombres de archivos.
Autor: Cirujano de Código
Descripción: Clasifica y divide PDFs de carpeta madre en subcarpetas específicas.
"""

import os
import sys
import re
import logging
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter

# Configuración de palabras clave
PALABRAS_CLAVE = {
    "1_Boletas": ["boleta", "boletas"],
    "2_Afp": ["afp"],
    "3_5ta": ["quinta"]
}

# Nombres base para archivos resultantes
NOMBRES_BASE = {
    "1_Boletas": "boleta",
    "2_Afp": "afp", 
    "3_5ta": "quinta"
}

def configurar_logging(carpeta_madre):
    """
    Configura el sistema de logging.
    
    Args:
        carpeta_madre (str): Carpeta donde se guardará el archivo de log.
    
    Returns:
        logging.Logger: Logger configurado.
    """
    # Crear nombre de archivo de log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(carpeta_madre, f"procesamiento_pdf_{timestamp}.log")
    
    # Configurar logging
    logger = logging.getLogger('pdf_processor')
    logger.setLevel(logging.INFO)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_filename

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

def preguntar_sobrescribir(carpetas_con_archivos):
    """
    Pregunta al usuario si desea sobrescribir archivos existentes.
    
    Args:
        carpetas_con_archivos (dict): Diccionario con carpetas que tienen archivos.
    
    Returns:
        bool: True si el usuario acepta sobrescribir, False si cancela.
    """
    if not carpetas_con_archivos:
        return True
    
    # Crear mensaje detallado
    mensaje = "Las siguientes carpetas destino contienen archivos:\n\n"
    for carpeta, cantidad in carpetas_con_archivos.items():
        nombre_carpeta = os.path.basename(carpeta)
        mensaje += f"• {nombre_carpeta}: {cantidad} archivo(s)\n"
    
    mensaje += "\n¿Desea continuar y sobrescribir los archivos existentes?"
    
    # Mostrar en consola
    print("\n" + "="*60)
    print("ADVERTENCIA: Carpetas con archivos existentes")
    print("="*60)
    for carpeta, cantidad in carpetas_con_archivos.items():
        nombre_carpeta = os.path.basename(carpeta)
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
    
    respuesta = messagebox.askyesno(
        "Advertencia - Archivos Existentes",
        mensaje
    )
    
    return respuesta

def buscar_pdfs_por_tipo(carpeta_madre, logger):
    """
    Busca PDFs en la carpeta madre y los clasifica por tipo.
    
    Args:
        carpeta_madre (str): Ruta de la carpeta madre.
        logger: Logger para registrar actividad.
    
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

def validar_unico_archivo_por_tipo(pdfs_por_tipo, logger):
    """
    Valida que haya solo un archivo PDF por cada tipo.
    
    Args:
        pdfs_por_tipo (dict): Diccionario con PDFs clasificados por tipo.
        logger: Logger para registrar actividad.
    
    Returns:
        bool: True si hay máximo 1 archivo por tipo, False si hay múltiples.
    """
    tipos_problematicos = []
    
    for tipo, archivos in pdfs_por_tipo.items():
        if len(archivos) > 1:
            tipos_problematicos.append((tipo, archivos))
            logger.warning(f"Múltiples archivos para {tipo}: {len(archivos)} encontrados")
    
    if tipos_problematicos:
        # Crear mensaje de error
        mensaje = "Se encontraron múltiples archivos para los siguientes tipos:\n\n"
        for tipo, archivos in tipos_problematicos:
            nombre_base = NOMBRES_BASE.get(tipo, tipo)
            mensaje += f"• {nombre_base.upper()} ({tipo}):\n"
            for archivo in archivos:
                mensaje += f"    - {archivo}\n"
            mensaje += "\n"
        
        mensaje += "Solo se permite un archivo por tipo. Por favor, revise los archivos."
        
        # Mostrar en consola
        print("\n" + "="*60)
        print("ERROR: Múltiples archivos encontrados")
        print("="*60)
        for tipo, archivos in tipos_problematicos:
            print(f"\n{tipo}:")
            for archivo in archivos:
                print(f"  • {archivo}")
        print("="*60)
        
        # Mostrar diálogo gráfico
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showerror(
            "Error - Múltiples Archivos",
            mensaje
        )
        
        return False
    
    return True

def dividir_pdf(ruta_pdf, carpeta_destino, nombre_base, logger):
    """
    Divide un PDF en páginas individuales.
    
    Args:
        ruta_pdf (str): Ruta del PDF a dividir.
        carpeta_destino (str): Carpeta donde guardar las páginas.
        nombre_base (str): Nombre base para los archivos resultantes.
        logger: Logger para registrar actividad.
    
    Returns:
        tuple: (éxito, páginas_procesadas, mensaje_error)
    """
    try:
        # Verificar que el PDF existe
        if not os.path.exists(ruta_pdf):
            return False, 0, f"Archivo no encontrado: {ruta_pdf}"
        
        # Leer PDF
        with open(ruta_pdf, 'rb') as file:
            reader = PdfReader(file)
            
            # Verificar si está encriptado
            if reader.is_encrypted:
                return False, 0, f"PDF protegido con contraseña: {os.path.basename(ruta_pdf)}"
            
            num_paginas = len(reader.pages)
            logger.info(f"  Dividiendo '{os.path.basename(ruta_pdf)}' ({num_paginas} páginas)")
            
            # Crear carpeta destino si no existe
            os.makedirs(carpeta_destino, exist_ok=True)
            
            # Dividir en páginas individuales
            paginas_procesadas = 0
            for i, page in enumerate(reader.pages):
                # Crear nombre de archivo
                nombre_archivo = f"{nombre_base}_{i+1}.pdf"
                ruta_salida = os.path.join(carpeta_destino, nombre_archivo)
                
                # Crear PDF de una sola página
                writer = PdfWriter()
                writer.add_page(page)
                
                # Guardar página individual
                with open(ruta_salida, 'wb') as output_file:
                    writer.write(output_file)
                
                paginas_procesadas += 1
            
            logger.info(f"  ✓ {paginas_procesadas} páginas creadas en {carpeta_destino}")
            return True, paginas_procesadas, None
            
    except PyPDF2.errors.PdfReadError as e:
        return False, 0, f"Error al leer PDF (posiblemente corrupto): {str(e)}"
    except Exception as e:
        return False, 0, f"Error inesperado: {str(e)}"

def limpiar_carpeta_destino(carpeta_destino, logger):
    """
    Elimina todos los archivos de una carpeta destino.
    
    Args:
        carpeta_destino (str): Ruta de la carpeta a limpiar.
        logger: Logger para registrar actividad.
    """
    if os.path.exists(carpeta_destino):
        archivos = [f for f in os.listdir(carpeta_destino) 
                   if os.path.isfile(os.path.join(carpeta_destino, f))]
        
        for archivo in archivos:
            try:
                os.remove(os.path.join(carpeta_destino, archivo))
            except Exception as e:
                logger.error(f"Error al eliminar {archivo}: {str(e)}")
        
        if archivos:
            logger.info(f"  Limpiada carpeta: {carpeta_destino} ({len(archivos)} archivos eliminados)")

def procesar_pdfs(carpeta_madre, logger, sobrescribir=False):
    """
    Procesa todos los PDFs según las reglas establecidas.
    
    Args:
        carpeta_madre (str): Ruta de la carpeta madre.
        logger: Logger para registrar actividad.
        sobrescribir (bool): Si es True, sobrescribe archivos existentes.
    
    Returns:
        dict: Resumen del procesamiento.
    """
    logger.info("="*60)
    logger.info("INICIANDO PROCESAMIENTO DE PDFs")
    logger.info("="*60)
    
    # 1. Buscar y clasificar PDFs
    logger.info("Buscando y clasificando PDFs...")
    pdfs_por_tipo, pdfs_no_clasificados = buscar_pdfs_por_tipo(carpeta_madre, logger)
    
    # 2. Validar un solo archivo por tipo
    logger.info("Validando un solo archivo por tipo...")
    if not validar_unico_archivo_por_tipo(pdfs_por_tipo, logger):
        return {"error": "Múltiples archivos por tipo encontrados"}
    
    # 3. Verificar carpetas destino
    carpetas_destino = [os.path.join(carpeta_madre, tipo) for tipo in PALABRAS_CLAVE.keys()]
    carpetas_con_archivos = verificar_archivos_en_carpetas(carpetas_destino)
    
    if carpetas_con_archivos and not sobrescribir:
        logger.warning("Procesamiento cancelado por el usuario (archivos existentes)")
        return {"cancelado": "Usuario no aceptó sobrescribir"}
    
    # 4. Limpiar carpetas destino si se aceptó sobrescribir
    if sobrescribir:
        logger.info("Limpiando carpetas destino...")
        for carpeta in carpetas_destino:
            limpiar_carpeta_destino(carpeta, logger)
    
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
        exito, paginas, mensaje_error = dividir_pdf(ruta_pdf, carpeta_destino, nombre_base, logger)
        
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

def mostrar_resumen_final(resumen, carpeta_madre, log_filename):
    """
    Muestra un resumen final del procesamiento.
    
    Args:
        resumen (dict): Resumen del procesamiento.
        carpeta_madre (str): Ruta de la carpeta madre.
        log_filename (str): Ruta del archivo de log.
    """
    print("\n" + "="*60)
    print("RESUMEN DEL PROCESAMIENTO")
    print("="*60)
    
    if "error" in resumen:
        print(f"ERROR: {resumen['error']}")
        return
    
    if "cancelado" in resumen:
        print("PROCESAMIENTO CANCELADO")
        return
    
    print(f"PDFs procesados exitosamente: {resumen['pdfs_procesados']}")
    print(f"PDFs con errores: {resumen['pdfs_con_error']}")
    print(f"Total de páginas generadas: {resumen['total_paginas']}")
    print(f"PDFs no clasificados: {resumen.get('pdfs_no_clasificados', 0)}")
    
    print("\nDetalle por tipo:")
    for tipo, detalle in resumen.get("detalle_por_tipo", {}).items():
        nombre_base = NOMBRES_BASE.get(tipo, tipo)
        if detalle.get("procesado"):
            print(f"  • {nombre_base.upper()}: {detalle['archivo']} → {detalle['paginas']} páginas")
        else:
            if "error" in detalle:
                print(f"  • {nombre_base.upper()}: ERROR - {detalle['error']}")
            else:
                print(f"  • {nombre_base.upper()}: No procesado")
    
    if resumen.get("errores"):
        print("\nErrores encontrados:")
        for error in resumen["errores"]:
            print(f"  • {error['tipo']} - {error['archivo']}: {error['error']}")
    
    print(f"\nLog guardado en: {log_filename}")
    print("="*60)
    
    # Mostrar mensaje gráfico
    if resumen["pdfs_procesados"] > 0:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        mensaje = f"Procesamiento completado:\n\n"
        mensaje += f"• PDFs procesados: {resumen['pdfs_procesados']}\n"
        mensaje += f"• Páginas generadas: {resumen['total_paginas']}\n"
        mensaje += f"• PDFs con errores: {resumen['pdfs_con_error']}\n"
        mensaje += f"\nDetalles en: {os.path.basename(log_filename)}"
        
        messagebox.showinfo("Procesamiento Completado", mensaje)

def main():
    """
    Función principal del script.
    """
    print("="*60)
    print("DIVISOR DE PDFs POR PALABRAS CLAVE")
    print("="*60)
    print("Este script dividirá PDFs en páginas individuales según:")
    print("  • 'boleta(s)' → Carpeta 1_Boletas (archivos: boleta_1.pdf, boleta_2.pdf, ...)")
    print("  • 'afp' → Carpeta 2_Afp (archivos: afp_1.pdf, afp_2.pdf, ...)")
    print("  • 'quinta' → Carpeta 3_5ta (archivos: quinta_1.pdf, quinta_2.pdf, ...)")
    print("="*60)
    
    # Seleccionar carpeta madre (usando tkinter o argumento)
    if len(sys.argv) > 1:
        carpeta_madre = sys.argv[1]
    else:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        carpeta_madre = filedialog.askdirectory(
            title="Selecciona la carpeta madre con los PDFs"
        )
    
    if not carpeta_madre:
        print("\nOperación cancelada por el usuario.")
        return
    
    print(f"\nCarpeta madre seleccionada: {carpeta_madre}")
    
    # Configurar logging
    logger, log_filename = configurar_logging(carpeta_madre)
    logger.info(f"Iniciando procesamiento en carpeta: {carpeta_madre}")
    
    # Verificar archivos en carpetas destino
    carpetas_destino = [os.path.join(carpeta_madre, tipo) for tipo in PALABRAS_CLAVE.keys()]
    carpetas_con_archivos = verificar_archivos_en_carpetas(carpetas_destino)
    
    # Preguntar si se desea sobrescribir
    sobrescribir = preguntar_sobrescribir(carpetas_con_archivos)
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
    resumen = procesar_pdfs(carpeta_madre, logger, sobrescribir)
    
    # Mostrar resumen final
    mostrar_resumen_final(resumen, carpeta_madre, log_filename)
    
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