import os
import sys
from PyPDF2 import PdfReader, PdfWriter
# Importar logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger

# Inicializar logger
logger = Logger("CoreTools_DividirPDF")

# --- 1. Obtener Parámetros del Usuario ---
def obtener_parametros(ruta_pdf=None, hojas_por_pdf=None):
    """
    Si se pasa ruta_pdf (por ejemplo desde la GUI), la valida y la usa.
    Si se pasa hojas_por_pdf también se valida (debe ser convertible a int > 0).
    Si no se pasan, mantiene el comportamiento interactivo por consola.
    Retorna: (ruta_pdf, hojas_por_pdf) o (None, None) en caso de error/validación fallida.
    """
    logger.info("📝 Obteniendo parámetros de división")
    
    # ruta
    if ruta_pdf is None:
        ruta_pdf = input("➡️ Ingrese la ruta del archivo PDF a procesar (puede arrastrarlo aquí): ").strip()
    # limpieza
    ruta_pdf = ruta_pdf.strip().strip('"').strip("'")
    ruta_pdf = os.path.normpath(ruta_pdf)

    if not os.path.isfile(ruta_pdf):
        error_msg = f"No se encontró ningún archivo en la ruta: {ruta_pdf}"
        logger.error(error_msg)
        return None, None

    # hojas
    if hojas_por_pdf is None:
        # modo consola: pedimos al usuario
        while True:
            try:
                hojas = int(input("➡️ Ingrese la cantidad de hojas deseadas por PDF generado: "))
                if hojas <= 0:
                    print("⚠️ Error: La cantidad de hojas debe ser un número entero positivo.")
                    continue
                break
            except ValueError:
                print("⚠️ Error: Debe ingresar un número entero válido para la cantidad de hojas.")
    else:
        # fue pasado desde la GUI (o caller). Intentamos convertir y validar.
        try:
            hojas = int(hojas_por_pdf)
            if hojas <= 0:
                logger.error("La cantidad de hojas debe ser positiva")
                return None, None
        except Exception:
            logger.error("El parametro 'hojas_por_pdf' no es valido")
            return None, None

    logger.info(f"✅ PDF: {os.path.basename(ruta_pdf)}")
    logger.info(f"✅ Hojas por PDF: {hojas}")
    
    return ruta_pdf, hojas

# --- 2. Validar la División ---
def validar_division(ruta_pdf: str, hojas_por_pdf: int):
    """
    Valida que el PDF pueda dividirse exactamente.
    
    Args:
        ruta_pdf: Ruta del archivo PDF
        hojas_por_pdf: Número de páginas por archivo
        
    Returns:
        int: Número de PDFs a generar, o None si la validación falla
    """
    logger.info("🔍 Validando división de PDF...")
    
    try:
        with open(ruta_pdf, 'rb') as archivo_pdf:
            reader = PdfReader(archivo_pdf)
            total_hojas = len(reader.pages)

        logger.info(f"   Total de páginas: {total_hojas}")
        logger.info(f"   Páginas por archivo: {hojas_por_pdf}")

        if total_hojas == 0:
            logger.error("El PDF no contiene paginas")
            return None

        if total_hojas % hojas_por_pdf == 0:
            num_pdfs_a_generar = total_hojas // hojas_por_pdf
            logger.info(f"✅ Validación OK: Se generarán {num_pdfs_a_generar} archivos")
            return num_pdfs_a_generar
        else:
            residuo = total_hojas % hojas_por_pdf
            logger.error(f"Division inexacta: total={total_hojas}, por_pdf={hojas_por_pdf}, residuo={residuo}")
            return None

    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {ruta_pdf}")
        return None
    except Exception as e:
        logger.exception(f"Error al leer PDF: {e}")
        return None

# --- 3. Dividir y Guardar el PDF ---
def dividir_pdf(ruta_pdf: str, hojas_por_pdf: int, num_pdfs_a_generar: int, progress_callback=None):
    """
    Divide el PDF en múltiples archivos
    
    Args:
        ruta_pdf: Ruta del archivo PDF a dividir
        hojas_por_pdf: Número de páginas por archivo generado
        num_pdfs_a_generar: Cantidad de archivos PDF a generar
        progress_callback: Función opcional para reportar progreso (current, total)
        
    Returns:
        dict: Diccionario con resultado del proceso
    """
    logger.info("="*60)
    logger.info("📄 INICIANDO DIVISIÓN DE PDF")
    logger.info("="*60)
    logger.info(f"   Archivo: {os.path.basename(ruta_pdf)}")
    logger.info(f"   PDFs a generar: {num_pdfs_a_generar}")
    
    # 📁 Crear la carpeta dentro de la misma ubicación del PDF original
    directorio_pdf = os.path.dirname(ruta_pdf)
    BASE_DIR_SALIDA = os.path.join(directorio_pdf, "Archivos_Divididos")
    DIR_SALIDA = BASE_DIR_SALIDA
    contador = 1

    # Evitar sobrescribir carpetas previas
    while os.path.exists(DIR_SALIDA):
        DIR_SALIDA = f"{BASE_DIR_SALIDA}_{contador}"
        contador += 1

    os.makedirs(DIR_SALIDA, exist_ok=True)
    logger.info(f"📁 Carpeta de salida: {os.path.basename(DIR_SALIDA)}")
    
    pdfs_generados = 0
    errores = 0

    try:
        with open(ruta_pdf, 'rb') as archivo_pdf:
            reader = PdfReader(archivo_pdf)

            for i in range(num_pdfs_a_generar):
                try:
                    writer = PdfWriter()
                    inicio_pagina = i * hojas_por_pdf
                    fin_pagina = inicio_pagina + hojas_por_pdf

                    for j in range(inicio_pagina, fin_pagina):
                        writer.add_page(reader.pages[j])

                    nombre_archivo = f"Output_{i + 1}.pdf"
                    ruta_salida = os.path.join(DIR_SALIDA, nombre_archivo)

                    with open(ruta_salida, 'wb') as output_file:
                        writer.write(output_file)

                    pdfs_generados += 1
                    
                    # Log de progreso cada 10 archivos o al final
                    if pdfs_generados % 10 == 0 or pdfs_generados == num_pdfs_a_generar:
                        logger.info(f"   Progreso: {pdfs_generados}/{num_pdfs_a_generar}")
                    
                    # Llamar callback de progreso si existe
                    if progress_callback:
                        progress_callback(pdfs_generados, num_pdfs_a_generar)
                        
                except Exception as e:
                    logger.error(f"Error generando {nombre_archivo}: {e}")
                    errores += 1

        logger.info(f"✅ División completada: {pdfs_generados} archivos generados")
        if errores > 0:
            logger.warning(f"⚠️ {errores} errores durante el proceso")

        return {
            'success': True,
            'pdfs_generados': pdfs_generados,
            'carpeta_salida': DIR_SALIDA,
            'errores': errores
        }

    except Exception as e:
        logger.exception(f"Error durante la division: {e}")
        return {
            'success': False,
            'pdfs_generados': pdfs_generados,
            'carpeta_salida': DIR_SALIDA,
            'errores': errores + 1,
            'error_message': str(e)
        }

# --- 4. Función Principal ---
def procesar_pdfs(ruta_pdf=None, hojas_por_pdf=None, progress_callback=None):
    """
    Procesa la división de un PDF.
    - Si se pasan ruta_pdf y/o hojas_por_pdf, los usa.
    - Si no se pasan, funciona en modo consola interactivo.
    - progress_callback: función opcional para reportar progreso
    
    Returns:
        dict: Resultado del procesamiento (para uso desde GUI)
    """
    logger.info("="*70)
    logger.info("🚀 DIVISOR DE PDFs - INICIO")
    logger.info("="*70)
    
    print("=========================================")
    print("🚀 Divisor de PDFs")
    print("=========================================")

    ruta, hojas = obtener_parametros(ruta_pdf, hojas_por_pdf)
    
    # validar retorno
    if not ruta or not hojas:
        logger.error("❌ Parámetros inválidos")
        print("\n❌ Proceso abortado (parámetros inválidos o no proporcionados).")
        return {
            'success': False,
            'error_message': 'Parámetros inválidos'
        }

    num_pdfs = validar_division(ruta, hojas)

    if num_pdfs is not None:
        resultado = dividir_pdf(ruta, hojas, num_pdfs, progress_callback)

        logger.info("="*70)
        logger.info("📊 RESUMEN FINAL")
        logger.info("="*70)
        logger.info(f"✅ PDFs generados: {resultado['pdfs_generados']}")
        logger.error(f"❌ Errores: {resultado['errores']}")
        logger.info(f"📁 Ubicación: {resultado['carpeta_salida']}")
        logger.info("="*70)

        print("\n=========================================")
        print("🎉 ¡PROCESO COMPLETADO!")
        print("=========================================")
        print(f"Cantidad de PDFs Generados: {resultado['pdfs_generados']}")
        print(f"Errores: {resultado['errores']}")
        print(f"Archivos guardados en la carpeta: ✨ {resultado['carpeta_salida']} ✨")
        print("=========================================")
        
        return resultado
    else:
        logger.error("❌ Validación fallida")
        print("\n❌ Proceso abortado.")
        return {
            'success': False,
            'error_message': 'Validación fallida'
        }

# --- Ejecución del Programa ---
if __name__ == "__main__":
    logger.info("="*70)
    logger.info("📋 MODO STANDALONE - Divisor de PDFs")
    logger.info("="*70)
    
    try:
        procesar_pdfs()
        logger.info("✅ Proceso completado exitosamente")
    except Exception as e:
        logger.exception(f"Error critico: {e}")