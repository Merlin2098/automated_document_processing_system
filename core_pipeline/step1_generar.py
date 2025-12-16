#!/usr/bin/env python3
"""
Script para crear estructura de carpetas para proyecto de refactorización.
Autor: Cirujano de Código
Descripción: Crea las subcarpetas necesarias dentro de una carpeta de trabajo seleccionada por el usuario.
"""

import os
import sys
from PySide6.QtWidgets import QFileDialog, QApplication, QMessageBox

# Importar logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger

# Inicializar logger
logger = Logger("CorePipeline1_Generar")

def seleccionar_carpeta():
    """
    Muestra un diálogo para que el usuario seleccione la carpeta de trabajo.
    
    Returns:
        str: Ruta de la carpeta seleccionada o None si se cancela.
    """
    # Verificar si ya existe una instancia de QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    logger.info("📂 Abriendo diálogo de selección de carpeta...")
    print("Selecciona la carpeta de trabajo...")
    
    # Mostrar el diálogo de selección de carpeta
    carpeta_seleccionada = QFileDialog.getExistingDirectory(
        None,
        "Selecciona la carpeta de trabajo",
        "",
        QFileDialog.Option.ShowDirsOnly
    )
    
    if carpeta_seleccionada:
        logger.info(f"✅ Carpeta seleccionada: {carpeta_seleccionada}")
    else:
        logger.warning("⚠️ Usuario canceló la selección de carpeta")
    
    return carpeta_seleccionada if carpeta_seleccionada else None

def crear_estructura_carpetas(carpeta_base):
    """
    Crea la estructura de subcarpetas dentro de la carpeta base.
    
    Args:
        carpeta_base (str): Ruta de la carpeta principal donde se crearán las subcarpetas.
    
    Returns:
        tuple: (bool, list) - Éxito de la operación y lista de carpetas creadas/ya existentes.
    """
    logger.info("🏗️ Iniciando creación de estructura de carpetas")
    logger.info(f"📍 Carpeta base: {carpeta_base}")
    
    # Lista de subcarpetas a crear (en el orden especificado)
    subcarpetas = [
        "1_Boletas",
        "2_Afp", 
        "3_5ta",
        "4_Convocatoria",
        "5_CertificadosTrabajo"
    ]
    
    carpetas_creadas = []
    carpetas_existentes = []
    errores = []
    
    # Verificar que la carpeta base existe
    if not os.path.exists(carpeta_base):
        try:
            os.makedirs(carpeta_base)
            logger.info(f"✅ Carpeta base creada: {carpeta_base}")
            print(f"Carpeta base creada: {carpeta_base}")
        except Exception as e:
            error_msg = f"Error al crear carpeta base: {str(e)}"
            logger.error(error_msg)
            return False, [], [error_msg]
    
    # Crear cada subcarpeta
    logger.info(f"📋 Procesando {len(subcarpetas)} subcarpetas...")
    for subcarpeta in subcarpetas:
        ruta_completa = os.path.join(carpeta_base, subcarpeta)
        
        try:
            if os.path.exists(ruta_completa):
                carpetas_existentes.append(ruta_completa)
                logger.info(f"ℹ️ Carpeta ya existente: {subcarpeta}")
                print(f"✓ Carpeta ya existente: {subcarpeta}")
            else:
                os.makedirs(ruta_completa)
                carpetas_creadas.append(ruta_completa)
                logger.info(f"✅ Carpeta creada: {subcarpeta}")
                print(f"✓ Carpeta creada: {subcarpeta}")
        except Exception as e:
            error_msg = f"Error al crear '{subcarpeta}': {str(e)}"
            errores.append(error_msg)
            logger.error(error_msg)
            print(f"✗ {error_msg}")
    
    logger.info(f"📊 Resultado: {len(carpetas_creadas)} creadas, {len(carpetas_existentes)} existentes, {len(errores)} errores")
    return len(errores) == 0, carpetas_creadas, carpetas_existentes, errores

def mostrar_resumen(carpeta_base, carpetas_creadas, carpetas_existentes, errores):
    """
    Muestra un resumen detallado de la operación.
    
    Args:
        carpeta_base (str): Ruta de la carpeta principal.
        carpetas_creadas (list): Lista de carpetas creadas.
        carpetas_existentes (list): Lista de carpetas que ya existían.
        errores (list): Lista de errores encontrados.
    """
    logger.info("="*60)
    logger.info("📊 RESUMEN DE LA OPERACIÓN")
    logger.info("="*60)
    logger.info(f"Carpeta de trabajo: {carpeta_base}")
    logger.info(f"Carpetas creadas: {len(carpetas_creadas)}")
    logger.info(f"Carpetas ya existentes: {len(carpetas_existentes)}")
    logger.info(f"Errores: {len(errores)}")
    
    print("\n" + "="*60)
    print("RESUMEN DE LA OPERACIÓN")
    print("="*60)
    print(f"Carpeta de trabajo: {carpeta_base}")
    print(f"Carpetas creadas: {len(carpetas_creadas)}")
    print(f"Carpetas ya existentes: {len(carpetas_existentes)}")
    print(f"Errores: {len(errores)}")
    print("-"*60)
    
    if carpetas_creadas:
        logger.info("Carpetas creadas exitosamente:")
        print("\nCarpetas creadas exitosamente:")
        for carpeta in carpetas_creadas:
            logger.info(f"  • {os.path.basename(carpeta)}")
            print(f"  • {os.path.basename(carpeta)}")
    
    if carpetas_existentes:
        logger.info("Carpetas que ya existían:")
        print("\nCarpetas que ya existían:")
        for carpeta in carpetas_existentes:
            logger.info(f"  • {os.path.basename(carpeta)}")
            print(f"  • {os.path.basename(carpeta)}")
    
    if errores:
        logger.error("Errores encontrados:")
        print("\nErrores encontrados:")
        for error in errores:
            logger.error(f"  • {error}")
            print(f"  • {error}")
    
    logger.info("="*60)
    print("="*60)

def main():
    """
    Función principal del script.
    """
    logger.info("🚀 Iniciando Creador de Estructura de Carpetas")
    
    print("="*60)
    print("CREADOR DE ESTRUCTURA DE CARPETAS")
    print("="*60)
    print("Este script creará la siguiente estructura de carpetas:")
    print("  1. 1_Boletas")
    print("  2. 2_Afp")
    print("  3. 3_5ta")
    print("  4. 4_Convocatoria")
    print("  5. 5_CertificadosTrabajo")
    print("="*60)
    
    # Paso 1: Seleccionar carpeta de trabajo
    carpeta_base = seleccionar_carpeta()
    
    if not carpeta_base:
        logger.warning("⚠️ Operación cancelada por el usuario")
        print("\nOperación cancelada por el usuario.")
        return
    
    print(f"\nCarpeta seleccionada: {carpeta_base}")
    
    # Confirmar con el usuario
    respuesta = input(f"\n¿Crear estructura de carpetas en '{carpeta_base}'? (s/n): ").lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        logger.warning("⚠️ Usuario rechazó la confirmación")
        print("Operación cancelada.")
        return
    
    logger.info("✅ Usuario confirmó la operación")
    
    # Paso 2: Crear la estructura de carpetas
    print("\nCreando estructura de carpetas...")
    print("-"*60)
    
    exito, carpetas_creadas, carpetas_existentes, errores = crear_estructura_carpetas(carpeta_base)
    
    # Paso 3: Mostrar resumen
    mostrar_resumen(carpeta_base, carpetas_creadas, carpetas_existentes, errores)
    
    # Paso 4: Mostrar mensaje final
    if exito and not errores:
        logger.info("🎉 ¡Estructura de carpetas creada exitosamente!")
        print("\n✅ ¡Estructura de carpetas creada exitosamente!")
        print(f"\nPuedes comenzar a trabajar en: {carpeta_base}")
        
        # Mostrar mensaje gráfico si no hubo errores
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        QMessageBox.information(
            None,
            "Operación Exitosa",
            f"Estructura de carpetas creada exitosamente en:\n{carpeta_base}"
        )
    else:
        logger.warning("⚠️ La operación se completó con algunos errores")
        print("\n⚠️  La operación se completó con algunos errores.")
        if errores:
            print("Revisa los errores anteriores y corrige los problemas.")

def modo_linea_comandos(ruta_carpeta):
    """
    Modo alternativo para ejecutar desde línea de comandos con ruta específica.
    
    Args:
        ruta_carpeta (str): Ruta de la carpeta donde crear la estructura.
    """
    logger.info(f"🖥️ Modo línea de comandos - Carpeta: {ruta_carpeta}")
    print(f"\nModo línea de comandos - Carpeta especificada: {ruta_carpeta}")
    
    exito, carpetas_creadas, carpetas_existentes, errores = crear_estructura_carpetas(ruta_carpeta)
    
    mostrar_resumen(ruta_carpeta, carpetas_creadas, carpetas_existentes, errores)
    
    if exito and not errores:
        logger.info("🎉 ¡Estructura de carpetas creada exitosamente!")
        print("\n✅ ¡Estructura de carpetas creada exitosamente!")
    else:
        logger.error("❌ La operación se completó con errores")
        print("\n⚠️  La operación se completó con algunos errores.")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar si se proporcionó una ruta como argumento
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        if os.path.isabs(ruta) or os.path.exists(ruta):
            modo_linea_comandos(ruta)
        else:
            logger.error(f"❌ Ruta no válida: {ruta}")
            print(f"Error: La ruta '{ruta}' no es válida.")
            print("Usa: python crear_estructura.py [ruta_carpeta]")
            print("O ejecuta sin argumentos para usar el selector gráfico.")
    else:
        # Ejecutar en modo interactivo con interfaz gráfica
        main()