import os
from PyPDF2 import PdfReader, PdfWriter

# --- 1. Obtener Parámetros del Usuario ---
def obtener_parametros(ruta_pdf=None, hojas_por_pdf=None):
    """
    Si se pasa ruta_pdf (por ejemplo desde la GUI), la valida y la usa.
    Si se pasa hojas_por_pdf también se valida (debe ser convertible a int > 0).
    Si no se pasan, mantiene el comportamiento interactivo por consola.
    Retorna: (ruta_pdf, hojas_por_pdf) o (None, None) en caso de error/validación fallida.
    """
    # ruta
    if ruta_pdf is None:
        ruta_pdf = input("➡️ Ingrese la ruta del archivo PDF a procesar (puede arrastrarlo aquí): ").strip()
    # limpieza
    ruta_pdf = ruta_pdf.strip().strip('"').strip("'")
    ruta_pdf = os.path.normpath(ruta_pdf)

    if not os.path.isfile(ruta_pdf):
        print(f"⚠️ No se encontró ningún archivo en la ruta: {ruta_pdf}")
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
                print("⚠️ Error: La cantidad de hojas debe ser un número entero positivo.")
                return None, None
        except Exception:
            print("⚠️ Error: el parámetro 'hojas_por_pdf' no es un número válido.")
            return None, None

    return ruta_pdf, hojas

# --- 2. Validar la División ---
def validar_division(ruta_pdf: str, hojas_por_pdf: int):
    try:
        with open(ruta_pdf, 'rb') as archivo_pdf:
            reader = PdfReader(archivo_pdf)
            total_hojas = len(reader.pages)

        if total_hojas == 0:
            print("❌ Error: El PDF no contiene páginas.")
            return None

        if total_hojas % hojas_por_pdf == 0:
            num_pdfs_a_generar = total_hojas // hojas_por_pdf
            return num_pdfs_a_generar
        else:
            print(f"❌ Error: El total de hojas ({total_hojas}) no es divisible exactamente por la cantidad deseada ({hojas_por_pdf}).")
            print(f"   El residuo es: {total_hojas % hojas_por_pdf}. El proceso ha sido abortado.")
            return None

    except FileNotFoundError:
        print(f"❌ Error: El archivo en la ruta '{ruta_pdf}' no fue encontrado. Verifique la ruta.")
        return None
    except Exception as e:
        print(f"❌ Error al intentar leer el PDF: {e}")
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
                    
                    # Llamar callback de progreso si existe
                    if progress_callback:
                        progress_callback(pdfs_generados, num_pdfs_a_generar)
                        
                except Exception as e:
                    print(f"⚠️ Error generando {nombre_archivo}: {e}")
                    errores += 1

        return {
            'success': True,
            'pdfs_generados': pdfs_generados,
            'carpeta_salida': DIR_SALIDA,
            'errores': errores
        }

    except Exception as e:
        print(f"❌ Error durante el proceso de división: {e}")
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
    print("=========================================")
    print("🚀 Divisor de PDFs")
    print("=========================================")

    ruta, hojas = obtener_parametros(ruta_pdf, hojas_por_pdf)
    # validar retorno
    if not ruta or not hojas:
        print("\n❌ Proceso abortado (parámetros inválidos o no proporcionados).")
        return {
            'success': False,
            'error_message': 'Parámetros inválidos'
        }

    num_pdfs = validar_division(ruta, hojas)

    if num_pdfs is not None:
        resultado = dividir_pdf(ruta, hojas, num_pdfs, progress_callback)

        print("\n=========================================")
        print("🎉 ¡PROCESO COMPLETADO!")
        print("=========================================")
        print(f"Cantidad de PDFs Generados: {resultado['pdfs_generados']}")
        print(f"Errores: {resultado['errores']}")
        print(f"Archivos guardados en la carpeta: ✨ {resultado['carpeta_salida']} ✨")
        print("=========================================")
        
        return resultado
    else:
        print("\n❌ Proceso abortado.")
        return {
            'success': False,
            'error_message': 'Validación fallida'
        }

# --- Ejecución del Programa ---
if __name__ == "__main__":
    procesar_pdfs()