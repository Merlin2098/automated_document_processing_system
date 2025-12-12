import os
import json
from pathlib import Path
from tkinter import Tk, filedialog
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger
logger = Logger("CorePipeline4_Rename")

def seleccionar_carpeta_madre():
    """Abre un diálogo para seleccionar la carpeta madre."""
    root = Tk()
    root.withdraw()
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta madre")
    root.destroy()
    return carpeta

def cargar_json(ruta_json):
    """Carga el archivo JSON con manejo robusto de encodings."""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(ruta_json, 'r', encoding=encoding) as f:
                datos = json.load(f)
            print(f"  ✓ JSON cargado con encoding: {encoding}")
            logger.info(f"  ✓ JSON cargado con encoding: {encoding}")
            return datos
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as e:
            print(f"  ✗ Error en estructura JSON: {e}")
            logger.error(f"  ✗ Error en estructura JSON: {e}")
            return None
    
    print(f"  ✗ No se pudo leer el JSON con ningún encoding estándar")
    logger.error("  ✗ No se pudo leer el JSON con ningún encoding estándar")
    return None

def convertir_json_a_mapeo(datos_json):
    """
    Convierte la lista de diccionarios del JSON a un mapeo de renombrado.
    Maneja duplicados tomando solo la última ocurrencia.
    
    Args:
        datos_json: Lista de diccionarios con claves "ARCHIVO ORIGINAL" y "NUEVO NOMBRE"
    
    Returns:
        dict: {archivo_original: nuevo_nombre}
    """
    if not isinstance(datos_json, list):
        print(f"  ✗ Se esperaba una lista, se recibió: {type(datos_json).__name__}")
        logger.error(f"  ✗ Se esperaba una lista, se recibió: {type(datos_json).__name__}")
        return {}
    
    mapeo = {}
    duplicados = {}
    
    for idx, item in enumerate(datos_json):
        if not isinstance(item, dict):
            print(f"  ⚠ Item en posición {idx} no es un diccionario: {item}")
            continue
        
        # Obtener los valores
        archivo_original = item.get("ARCHIVO ORIGINAL")
        nuevo_nombre = item.get("NUEVO NOMBRE")
        
        if not archivo_original or not nuevo_nombre:
            print(f"  ⚠ Item en posición {idx} no tiene las claves esperadas: {item}")
            continue
        
        # Detectar duplicados
        if archivo_original in mapeo:
            if archivo_original not in duplicados:
                duplicados[archivo_original] = [mapeo[archivo_original]]
            duplicados[archivo_original].append(nuevo_nombre)
        
        # Guardar mapeo (si hay duplicados, se sobrescribe con el último)
        mapeo[archivo_original] = nuevo_nombre
    
    # Reportar duplicados
    if duplicados:
        print(f"\n  ⚠ ADVERTENCIA: Se encontraron {len(duplicados)} archivos con múltiples nombres:")
        logger.warning(f"  ⚠️ ADVERTENCIA: Se encontraron {len(duplicados)} archivos con múltiples nombres")
        mostrados = 0
        for original, nombres in duplicados.items():
            if mostrados < 5:  # Mostrar solo los primeros 5
                print(f"    • '{original}' → {len(nombres)} nombres diferentes")
                print(f"      Se usará: '{nombres[-1]}'")
                mostrados += 1
        if len(duplicados) > 5:
            print(f"    ... y {len(duplicados) - 5} archivos duplicados más")
        print(f"  → Se usará la última ocurrencia de cada archivo duplicado\n")
        logger.warning(f"  → Se usará la última ocurrencia de cada archivo duplicado")
    
    return mapeo

def renombrar_archivos(carpeta, mapeo):
    """
    Renombra los archivos según el mapeo proporcionado.
    
    Args:
        carpeta: Ruta de la carpeta donde están los PDFs
        mapeo: Diccionario {archivo_original: nuevo_nombre}
    
    Returns:
        tuple: (exitosos, fallidos, omitidos, total)
    """
    exitosos = 0
    fallidos = 0
    omitidos = 0
    errores = []
    advertencias = []
    
    for nombre_anterior, nombre_nuevo in mapeo.items():
        ruta_anterior = os.path.join(carpeta, nombre_anterior)
        ruta_nueva = os.path.join(carpeta, nombre_nuevo)
        
        # Verificar que el archivo original existe
        if not os.path.exists(ruta_anterior):
            errores.append(f"    ✗ No encontrado: {nombre_anterior}")
            logger.error(f"    ✗ No encontrado: {nombre_anterior}")
            fallidos += 1
            continue
        
        # Verificar que el destino no existe ya
        if os.path.exists(ruta_nueva):
            # Si el archivo destino ya existe, omitir
            advertencias.append(f"    ⚠ Ya existe: {nombre_nuevo}")
            logger.warning(f"    ⚠️ Ya existe: {nombre_nuevo}")
            omitidos += 1
            continue
        
        # Verificar si es el mismo nombre (no hace falta renombrar)
        if nombre_anterior == nombre_nuevo:
            advertencias.append(f"    → Mismo nombre: {nombre_anterior}")
            logger.info(f"    ✓ Renombrado: {nombre_anterior} → {nombre_nuevo}")
            omitidos += 1
            continue
        
        try:
            os.rename(ruta_anterior, ruta_nueva)
            exitosos += 1
        except Exception as e:
            errores.append(f"    ✗ Error al renombrar '{nombre_anterior}': {str(e)}")
            logger.error(f"    ✗ Error al renombrar '{nombre_anterior}': {str(e)}")
            fallidos += 1
    
    # Mostrar errores si los hay (máximo 10)
    if errores:
        print("\n  Errores encontrados:")
        for error in errores[:10]:
            print(error)
        if len(errores) > 10:
            print(f"    ... y {len(errores) - 10} errores más")
    
    # Mostrar advertencias si las hay (máximo 5)
    if advertencias:
        print("\n  Advertencias:")
        for adv in advertencias[:5]:
            print(adv)
        if len(advertencias) > 5:
            print(f"    ... y {len(advertencias) - 5} advertencias más")
    
    return exitosos, fallidos, omitidos, len(mapeo)

def procesar_lote(carpeta_lote):
    """
    Procesa una carpeta (lote) buscando el JSON y renombrando archivos.
    
    Returns:
        dict: Estadísticas del procesamiento
    """
    nombre_lote = os.path.basename(carpeta_lote)
    print(f"\n{'='*60}")
    print(f"Procesando lote: {nombre_lote}")
    print(f"{'='*60}")
    logger.info("="*60)
    logger.info(f"Procesando lote: {nombre_lote}")
    logger.info("="*60)
    
    # Buscar archivo JSON
    archivos_json = [f for f in os.listdir(carpeta_lote) if f.endswith('.json')]
    
    if not archivos_json:
        print("  ⚠ No se encontró archivo JSON en este lote")
        logger.warning("  ⚠️ No se encontró archivo JSON en este lote")
        return {
            'lote': nombre_lote,
            'exitosos': 0,
            'fallidos': 0,
            'omitidos': 0,
            'total': 0,
            'estado': 'sin_json'
        }
    
    if len(archivos_json) > 1:
        print(f"  ⚠ Se encontraron múltiples JSON: {archivos_json}")
        print(f"  → Se usará: {archivos_json[0]}")
        logger.warning(f"  ⚠️ Se encontraron múltiples JSON: {archivos_json}")
        logger.info(f"  → Se usará: {archivos_json[0]}")
    
    ruta_json = os.path.join(carpeta_lote, archivos_json[0])
    print(f"  JSON encontrado: {archivos_json[0]}")
    logger.info(f"  JSON encontrado: {archivos_json[0]}")
    
    # Cargar datos del JSON
    datos_json = cargar_json(ruta_json)
    
    if datos_json is None:
        return {
            'lote': nombre_lote,
            'exitosos': 0,
            'fallidos': 0,
            'omitidos': 0,
            'total': 0,
            'estado': 'json_invalido'
        }
    
    if not datos_json:
        print("  ⚠ El archivo JSON está vacío")
        logger.warning("  ⚠️ El archivo JSON está vacío")
        return {
            'lote': nombre_lote,
            'exitosos': 0,
            'fallidos': 0,
            'omitidos': 0,
            'total': 0,
            'estado': 'json_vacio'
        }
    
    print(f"  → Registros en JSON: {len(datos_json)}")
    
    # Convertir a mapeo
    mapeo = convertir_json_a_mapeo(datos_json)
    
    if not mapeo:
        print("  ✗ No se pudo generar mapeo de renombrado")
        return {
            'lote': nombre_lote,
            'exitosos': 0,
            'fallidos': 0,
            'omitidos': 0,
            'total': 0,
            'estado': 'mapeo_vacio'
        }
    
    print(f"  → Archivos únicos a procesar: {len(mapeo)}")
    
    # Ejecutar renombrado
    exitosos, fallidos, omitidos, total = renombrar_archivos(carpeta_lote, mapeo)
    
    print(f"\n  Resultados del lote:")
    print(f"    ✓ Exitosos: {exitosos}")
    print(f"    ✗ Fallidos: {fallidos}")
    print(f"    ⊘ Omitidos: {omitidos}")
    print(f"    Total: {total}")
    
    return {
        'lote': nombre_lote,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'omitidos': omitidos,
        'total': total,
        'estado': 'procesado'
    }

def main():
    print("\n" + "="*60)
    print(" RENOMBRADO MASIVO DE ARCHIVOS POR LOTES")
    print("="*60)
    logger.info("="*60)
    logger.info(" RENOMBRADO MASIVO DE ARCHIVOS POR LOTES")
    logger.info("="*60)
    
    # Seleccionar carpeta madre
    carpeta_madre = seleccionar_carpeta_madre()
    
    if not carpeta_madre:
        print("\n✗ No se seleccionó ninguna carpeta. Proceso cancelado.")
        logger.warning("✗ No se seleccionó ninguna carpeta. Proceso cancelado.")
        return
    
    print(f"\nCarpeta seleccionada: {carpeta_madre}")
    logger.info(f"Carpeta seleccionada: {carpeta_madre}")
    
    # Definir las carpetas a procesar
    carpetas_a_procesar = ['1_Boletas', '2_Afp', '3_5ta', '4_Convocatoria', '5_CertificadosTrabajo']
    
    # Estadísticas globales
    estadisticas = []
    
    # Procesar cada lote
    for nombre_carpeta in carpetas_a_procesar:
        ruta_lote = os.path.join(carpeta_madre, nombre_carpeta)
        
        if not os.path.exists(ruta_lote):
            print(f"\n⚠ La carpeta '{nombre_carpeta}' no existe. Se omite.")
            estadisticas.append({
                'lote': nombre_carpeta,
                'exitosos': 0,
                'fallidos': 0,
                'omitidos': 0,
                'total': 0,
                'estado': 'no_existe'
            })
            continue
        
        if not os.path.isdir(ruta_lote):
            print(f"\n⚠ '{nombre_carpeta}' no es una carpeta. Se omite.")
            continue
        
        # Procesar el lote
        resultado = procesar_lote(ruta_lote)
        estadisticas.append(resultado)
    
    # Resumen final
    print("\n" + "="*60)
    print(" RESUMEN FINAL")
    print("="*60)
    logger.info("="*60)
    logger.info(" RESUMEN FINAL")
    logger.info("="*60)
    
    total_exitosos = sum(e['exitosos'] for e in estadisticas)
    total_fallidos = sum(e['fallidos'] for e in estadisticas)
    total_omitidos = sum(e['omitidos'] for e in estadisticas)
    total_archivos = sum(e['total'] for e in estadisticas)
    
    print(f"\nLotes procesados: {len(estadisticas)}")
    print(f"\nResultados globales:")
    print(f"  ✓ Archivos renombrados exitosamente: {total_exitosos}")
    print(f"  ✗ Archivos con errores: {total_fallidos}")
    print(f"  ⊘ Archivos omitidos: {total_omitidos}")
    print(f"  Total de archivos procesados: {total_archivos}")
    logger.info(f"  ✓ Archivos renombrados exitosamente: {total_exitosos}")
    logger.info(f"  ✗ Archivos con errores: {total_fallidos}")
    logger.info(f"  ⊘ Archivos omitidos: {total_omitidos}")
    
    if total_archivos > 0:
        porcentaje = (total_exitosos / total_archivos) * 100
        print(f"  Tasa de éxito: {porcentaje:.1f}%")
    
    # Detalle por lote
    print(f"\nDetalle por lote:")
    for stat in estadisticas:
        if stat['total'] > 0:
            tasa = (stat['exitosos'] / stat['total']) * 100
            print(f"  • {stat['lote']}: {stat['exitosos']}/{stat['total']} ({tasa:.1f}%) | Fallidos: {stat['fallidos']} | Omitidos: {stat['omitidos']}")
        else:
            print(f"  • {stat['lote']}: {stat['estado']}")
    
    print("\n" + "="*60)
    print(" PROCESO COMPLETADO")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()