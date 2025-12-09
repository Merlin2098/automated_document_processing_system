#!/usr/bin/env python3
"""
Script para crear estructura de carpetas para proyecto de refactorización.
Autor: Cirujano de Código
Descripción: Crea las subcarpetas necesarias dentro de una carpeta de trabajo seleccionada por el usuario.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

def seleccionar_carpeta():
    """
    Muestra un diálogo para que el usuario seleccione la carpeta de trabajo.
    
    Returns:
        str: Ruta de la carpeta seleccionada o None si se cancela.
    """
    # Ocultar la ventana principal de tkinter
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Mantener la ventana encima de otras
    
    print("Selecciona la carpeta de trabajo...")
    
    # Mostrar el diálogo de selección de carpeta
    carpeta_seleccionada = filedialog.askdirectory(
        title="Selecciona la carpeta de trabajo"
    )
    
    return carpeta_seleccionada if carpeta_seleccionada else None

def crear_estructura_carpetas(carpeta_base):
    """
    Crea la estructura de subcarpetas dentro de la carpeta base.
    
    Args:
        carpeta_base (str): Ruta de la carpeta principal donde se crearán las subcarpetas.
    
    Returns:
        tuple: (bool, list) - Éxito de la operación y lista de carpetas creadas/ya existentes.
    """
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
            print(f"Carpeta base creada: {carpeta_base}")
        except Exception as e:
            return False, [], [f"Error al crear carpeta base: {str(e)}"]
    
    # Crear cada subcarpeta
    for subcarpeta in subcarpetas:
        ruta_completa = os.path.join(carpeta_base, subcarpeta)
        
        try:
            if os.path.exists(ruta_completa):
                carpetas_existentes.append(ruta_completa)
                print(f"✓ Carpeta ya existente: {subcarpeta}")
            else:
                os.makedirs(ruta_completa)
                carpetas_creadas.append(ruta_completa)
                print(f"✓ Carpeta creada: {subcarpeta}")
        except Exception as e:
            errores.append(f"Error al crear '{subcarpeta}': {str(e)}")
            print(f"✗ Error al crear '{subcarpeta}': {str(e)}")
    
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
    print("\n" + "="*60)
    print("RESUMEN DE LA OPERACIÓN")
    print("="*60)
    print(f"Carpeta de trabajo: {carpeta_base}")
    print(f"Carpetas creadas: {len(carpetas_creadas)}")
    print(f"Carpetas ya existentes: {len(carpetas_existentes)}")
    print(f"Errores: {len(errores)}")
    print("-"*60)
    
    if carpetas_creadas:
        print("\nCarpetas creadas exitosamente:")
        for carpeta in carpetas_creadas:
            print(f"  • {os.path.basename(carpeta)}")
    
    if carpetas_existentes:
        print("\nCarpetas que ya existían:")
        for carpeta in carpetas_existentes:
            print(f"  • {os.path.basename(carpeta)}")
    
    if errores:
        print("\nErrores encontrados:")
        for error in errores:
            print(f"  • {error}")
    
    print("="*60)

def main():
    """
    Función principal del script.
    """
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
        print("\nOperación cancelada por el usuario.")
        return
    
    print(f"\nCarpeta seleccionada: {carpeta_base}")
    
    # Confirmar con el usuario
    respuesta = input(f"\n¿Crear estructura de carpetas en '{carpeta_base}'? (s/n): ").lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("Operación cancelada.")
        return
    
    # Paso 2: Crear la estructura de carpetas
    print("\nCreando estructura de carpetas...")
    print("-"*60)
    
    exito, carpetas_creadas, carpetas_existentes, errores = crear_estructura_carpetas(carpeta_base)
    
    # Paso 3: Mostrar resumen
    mostrar_resumen(carpeta_base, carpetas_creadas, carpetas_existentes, errores)
    
    # Paso 4: Mostrar mensaje final
    if exito and not errores:
        print("\n✅ ¡Estructura de carpetas creada exitosamente!")
        print(f"\nPuedes comenzar a trabajar en: {carpeta_base}")
        
        # Mostrar mensaje gráfico si no hubo errores
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Operación Exitosa",
            f"Estructura de carpetas creada exitosamente en:\n{carpeta_base}"
        )
    else:
        print("\n⚠️  La operación se completó con algunos errores.")
        if errores:
            print("Revisa los errores anteriores y corrige los problemas.")

def modo_linea_comandos(ruta_carpeta):
    """
    Modo alternativo para ejecutar desde línea de comandos con ruta específica.
    
    Args:
        ruta_carpeta (str): Ruta de la carpeta donde crear la estructura.
    """
    print(f"\nModo línea de comandos - Carpeta especificada: {ruta_carpeta}")
    
    exito, carpetas_creadas, carpetas_existentes, errores = crear_estructura_carpetas(ruta_carpeta)
    
    mostrar_resumen(ruta_carpeta, carpetas_creadas, carpetas_existentes, errores)
    
    if exito and not errores:
        print("\n✅ ¡Estructura de carpetas creada exitosamente!")
    else:
        print("\n⚠️  La operación se completó con algunos errores.")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar si se proporcionó una ruta como argumento
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        if os.path.isabs(ruta) or os.path.exists(ruta):
            modo_linea_comandos(ruta)
        else:
            print(f"Error: La ruta '{ruta}' no es válida.")
            print("Usa: python crear_estructura.py [ruta_carpeta]")
            print("O ejecuta sin argumentos para usar el selector gráfico.")
    else:
        # Ejecutar en modo interactivo con interfaz gráfica
        main()