"""
Flujo combinado: Extracción de PDFs y generación directa de Excel
OPTIMIZADO: write_only + numpy + DuckDB + multiprocessing
"""

import os
import sys
import time
import gc
from typing import List, Dict, Optional, Tuple
from multiprocessing import Pool, cpu_count
from utils.logger import Logger

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar extractores específicos
from extractores.extractor_afp import extraer_datos_afp
from extractores.extractor_boleta import extraer_datos_boleta
from extractores.extractor_quinta import extraer_datos_quinta

logger = Logger("CorePipeline3_Diagnostico")

# ============================================
# CONFIGURACIÓN DE CARPETAS Y TIPOS
# ============================================

CARPETAS_CONFIG = {
    "1_Boletas": {
        "tipo": "BOLETA",
        "extractor": extraer_datos_boleta,
        "campos_extra": ["fecha_extraida"],
        "nombre_hoja": "1_Boletas"
    },
    "2_Afp": {
        "tipo": "AFP",
        "extractor": extraer_datos_afp,
        "campos_extra": [],
        "nombre_hoja": "2_Afp"
    },
    "3_5ta": {
        "tipo": "QUINTA",
        "extractor": extraer_datos_quinta,
        "campos_extra": [],
        "nombre_hoja": "3_5ta"
    },
    "4_Convocatoria": {
        "tipo": "CONVOCATORIA",
        "extractor": None,  # Solo listado de archivos
        "campos_extra": [],
        "nombre_hoja": "1ERA"
    },
    "5_CertificadosTrabajo": {
        "tipo": "CERTIFICADO_TRABAJO",
        "extractor": None,  # Solo listado de archivos
        "campos_extra": [],
        "nombre_hoja": "CTRA"
    }
}

# Tamaño del lote para progreso
BATCH_SIZE = 100

# ============================================
# FUNCIONES DE PROCESAMIENTO (MULTIPROCESSING)
# ============================================

def procesar_carpeta_mp(args: Tuple[str, str, str, str]) -> Tuple[str, str, float, List[str]]:
    """
    Procesa una carpeta completa en un proceso separado (SPAWN-SAFE).
    Re-importa extractores dentro del subproceso para compatibilidad Windows.
    Retorna: (nombre_carpeta, ruta_parquet, tiempo_procesamiento, logs)
    """
    nombre_carpeta, ruta_carpeta, tipo_documento, ruta_parquet = args
    import re
    
    # RE-IMPORTAR extractores dentro del subproceso (Windows spawn-safe)
    from extractores.extractor_afp import extraer_datos_afp
    from extractores.extractor_boleta import extraer_datos_boleta
    from extractores.extractor_quinta import extraer_datos_quinta
    
    # Mapeo de tipos a extractores
    EXTRACTORES_MAP = {
        "BOLETA": extraer_datos_boleta,
        "AFP": extraer_datos_afp,
        "QUINTA": extraer_datos_quinta,
        "CONVOCATORIA": None,
        "CERTIFICADO_TRABAJO": None
    }
    
    inicio = time.time()
    registros = []
    logs = []
    extractor = EXTRACTORES_MAP.get(tipo_documento)

    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.pdf')]
    
    # Ordenar archivos numéricamente por el número después del guión bajo
    def extraer_numero(filename):
        match = re.search(r'_(\d+)', filename)
        return int(match.group(1)) if match else 0
    
    archivos_pdf.sort(key=extraer_numero)

    logs.append(f"📂 Procesando: {nombre_carpeta}")
    logs.append(f"   Tipo: {tipo_documento} | PDFs: {len(archivos_pdf)}")

    # Si no hay extractor, solo listar archivos
    if extractor is None:
        for idx, archivo in enumerate(archivos_pdf, 1):
            registro = {"archivo": archivo}
            registros.append(registro)
            
            if idx % BATCH_SIZE == 0:
                logs.append(f"   Listados: {idx}/{len(archivos_pdf)}")
    else:
        # Procesar con extractor + validación post-extracción
        exitos = 0
        fallos = 0
        for idx, archivo in enumerate(archivos_pdf, 1):
            ruta_completa = os.path.join(ruta_carpeta, archivo)
            resultado = extractor(ruta_completa)

            registro = {
                "archivo_original": archivo,
                "tipo_documento": tipo_documento,
                "nombre_extraido": resultado.get("nombre"),
                "dni_extraido": resultado.get("dni")
            }

            if "fecha" in resultado and resultado["fecha"]:
                registro["fecha_extraida"] = resultado["fecha"]

            # Validación post-extracción: detectar fallos diagnósticamente
            if not resultado.get("exito", False):
                fallos += 1
                obs = resultado.get("observaciones", "Sin detalle")
                registro["observaciones"] = obs
                logs.append(f"   ⚠️ Fallo extracción: {archivo} → {obs}")
            else:
                exitos += 1

            registros.append(registro)

            if idx % BATCH_SIZE == 0:
                logs.append(f"   Procesados: {idx}/{len(archivos_pdf)}")

        # Resumen de validación por carpeta
        logs.append(f"   📊 Resumen: {exitos} exitosos, {fallos} fallidos de {len(archivos_pdf)} PDFs")

    # Escribir Parquet inmediatamente
    try:
        import pandas as pd
        if registros:
            df = pd.DataFrame(registros)
            df.to_parquet(ruta_parquet, engine='pyarrow', compression='snappy', index=False)
            logs.append(f"   💾 Parquet: {os.path.basename(ruta_parquet)}")
            del df
    except Exception as e:
        logs.append(f"   ⚠️ Error Parquet: {e}")

    fin = time.time()
    tiempo_total = fin - inicio
    logs.append(f"   ✅ {len(registros)} registros en {int(tiempo_total // 60)}m {int(tiempo_total % 60)}s")
    
    # Liberar memoria explícitamente
    del registros
    gc.collect()
    
    return (nombre_carpeta, ruta_parquet, tiempo_total, logs)


def procesar_carpetas_paralelo(ruta_carpeta_trabajo: str, nombre_base_excel: str, 
                               progress_callback=None) -> Dict[str, str]:
    """
    Procesa todas las carpetas en paralelo usando multiprocessing.
    Retorna diccionario con rutas de Parquets generados.
    """
    # Preparar argumentos para cada carpeta (spawn-safe: solo datos serializables)
    tareas = []
    carpetas_validas = []
    
    for nombre_carpeta, config in CARPETAS_CONFIG.items():
        ruta_subcarpeta = os.path.join(ruta_carpeta_trabajo, nombre_carpeta)
        if not os.path.isdir(ruta_subcarpeta):
            logger.warning(f"⚠️ Carpeta '{nombre_carpeta}' no encontrada, omitiendo...")
            continue
        
        nombre_parquet = f"{nombre_base_excel}_{nombre_carpeta}.parquet"
        ruta_parquet = os.path.join(ruta_carpeta_trabajo, nombre_parquet)
        
        # Pasar solo tipo_documento (string) en lugar del config completo (spawn-safe)
        tipo_documento = config["tipo"]
        tareas.append((nombre_carpeta, ruta_subcarpeta, tipo_documento, ruta_parquet))
        carpetas_validas.append(nombre_carpeta)
    
    if not tareas:
        logger.error("No hay carpetas válidas para procesar")
        return {}
    
    total_carpetas = len(tareas)
    logger.info(f"🚀 Iniciando procesamiento paralelo de {total_carpetas} carpetas")
    print(f"\n🚀 Procesando {total_carpetas} carpetas en paralelo...")
    
    # Determinar número de workers (máximo 5 carpetas)
    num_workers = min(cpu_count(), total_carpetas)
    
    rutas_parquet = {}
    carpetas_completadas = 0
    inicio_global = time.time()
    
    # Procesar en paralelo
    with Pool(processes=num_workers) as pool:
        for resultado in pool.imap_unordered(procesar_carpeta_mp, tareas):
            nombre_carpeta, ruta_parquet, tiempo_carpeta, logs = resultado
            
            # Consolidar logs
            for log_line in logs:
                logger.info(log_line)
                print(log_line)

            rutas_parquet[nombre_carpeta] = ruta_parquet
            carpetas_completadas += 1

            # Reportar progreso global (incluir logs para que el worker los surfacee)
            if progress_callback:
                progress_callback(carpetas_completadas, total_carpetas, tiempo_carpeta, logs)
            
            print(f"\n📊 Progreso global: {carpetas_completadas}/{total_carpetas} carpetas completadas")
            logger.info(f"📊 Progreso: {carpetas_completadas}/{total_carpetas} carpetas")
    
    tiempo_total_global = time.time() - inicio_global
    print(f"\n✅ Todas las carpetas procesadas en {int(tiempo_total_global // 60)}m {int(tiempo_total_global % 60)}s")
    logger.info(f"✅ Procesamiento paralelo completado en {int(tiempo_total_global // 60)}m {int(tiempo_total_global % 60)}s")
    
    return rutas_parquet


# ============================================
# FUNCIONES DE EXCEL OPTIMIZADAS
# ============================================

def generar_excel_streaming(rutas_parquet: Dict[str, str], ruta_excel: str) -> bool:
    """
    Genera Excel con modo write_only para máximo rendimiento.
    Usa DuckDB para leer Parquet y numpy para escritura rápida.
    """
    try:
        import duckdb
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        
        inicio = time.time()
        logger.info("📊 Generando Excel en modo streaming...")
        print("\n📊 Generando Excel optimizado...")

        # Crear workbook en modo write_only
        wb = openpyxl.Workbook(write_only=True)
        
        # Estilos para encabezado
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        for nombre_carpeta, ruta_parquet in rutas_parquet.items():
            if not os.path.exists(ruta_parquet):
                logger.warning(f"⚠️ Parquet no encontrado: {ruta_parquet}")
                continue
            
            # Leer con DuckDB (más rápido que pandas)
            df = duckdb.read_parquet(ruta_parquet).df()
            # Convertir pd.NA → None (openpyxl no soporta pd.NA)
            df = df.where(df.notna(), None)
            
            if df.empty:
                logger.warning(f"⚠️ DataFrame vacío para {nombre_carpeta}")
                del df
                gc.collect()
                continue
            
            # Obtener nombre de hoja
            config = CARPETAS_CONFIG.get(nombre_carpeta, {})
            nombre_hoja = config.get("nombre_hoja", nombre_carpeta)
            
            ws = wb.create_sheet(title=nombre_hoja)
            
            # Detectar tipo de hoja
            es_listado_simple = len(df.columns) == 1 and "archivo" in df.columns
            
            # Escribir encabezado con estilo
            header_row = []
            for col_name in df.columns:
                cell = openpyxl.cell.cell.WriteOnlyCell(ws)
                if es_listado_simple:
                    cell.value = "ARCHIVO"
                else:
                    cell.value = col_name.replace("_", " ").upper()
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                header_row.append(cell)
            
            ws.append(header_row)
            
            # Establecer anchos de columna fijos (Opción B)
            if es_listado_simple:
                ws.column_dimensions['A'].width = 25
            else:
                anchos_estandar = {
                    'A': 25,  # archivo_original
                    'B': 20,  # tipo_documento o nombre
                    'C': 20,  # nombre_extraido o dni
                    'D': 15,  # dni_extraido
                    'E': 15   # fecha_extraida
                }
                for col_letter, ancho in anchos_estandar.items():
                    ws.column_dimensions[col_letter].width = ancho
            
            # Convertir a numpy y escribir por lotes (MUCHO más rápido)
            datos_numpy = df.to_numpy().tolist()
            for row in datos_numpy:
                ws.append(row)
            
            logger.info(f"   ✅ Hoja '{nombre_hoja}' escrita ({len(df)} registros)")
            print(f"   ✅ Hoja '{nombre_hoja}': {len(df)} registros")
            
            # Liberar memoria inmediatamente
            del df
            del datos_numpy
            gc.collect()
        
        # Guardar workbook
        wb.save(ruta_excel)
        
        tiempo_excel = time.time() - inicio
        print(f"\n✅ Excel generado en {int(tiempo_excel)}s: {ruta_excel}")
        logger.info(f"✅ Excel generado en {int(tiempo_excel)}s")
        
        return True

    except ImportError as e:
        logger.error(f"⚠️ Dependencia faltante: {e}")
        print(f"⚠️ Instale: pip install duckdb openpyxl pyarrow")
        return False
    except Exception as e:
        logger.error(f"❌ Error generando Excel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"❌ Error: {e}")
        return False


# ============================================
# FUNCIÓN PRINCIPAL OPTIMIZADA
# ============================================

def procesar_diagnostico_a_excel(ruta_carpeta_trabajo: str, ruta_excel_final: str, 
                                progress_callback=None, guardar_json_opcional: bool = False):
    """
    Procesa PDFs en paralelo y genera Excel optimizado.
    Usa multiprocessing + write_only + numpy + DuckDB para máximo rendimiento.
    """
    print("="*60)
    print("🚀 DIAGNÓSTICO OPTIMIZADO - MODO PARALELO")
    print("="*60)
    logger.info("="*60)
    logger.info("🚀 DIAGNÓSTICO OPTIMIZADO - MODO PARALELO")
    logger.info("="*60)

    if not os.path.isdir(ruta_carpeta_trabajo):
        logger.error(f"❌ Carpeta '{ruta_carpeta_trabajo}' no existe")
        print(f"❌ Carpeta no encontrada")
        return
    
    # Extraer nombre base del Excel
    nombre_base_excel = os.path.splitext(os.path.basename(ruta_excel_final))[0]
    
    # FASE 1: Procesamiento paralelo de carpetas
    rutas_parquet = procesar_carpetas_paralelo(
        ruta_carpeta_trabajo, 
        nombre_base_excel,
        progress_callback
    )
    
    if not rutas_parquet:
        logger.error("❌ No se generaron Parquets")
        print("❌ Sin datos para procesar")
        return
    
    # FASE 2: Generar Excel streaming
    exito = generar_excel_streaming(rutas_parquet, ruta_excel_final)
    
    if exito:
        print("\n✅ Proceso completado exitosamente")
        logger.info("✅ Proceso completado")
        logger.info("📁 Archivos .parquet mantenidos en carpeta de trabajo (política empresarial)")
    else:
        logger.error("❌ Error en generación de Excel")
        print("❌ Fallo en generación de Excel")


# ============================================
# OBTENER RUTA DE CARPETA
# ============================================

def obtener_ruta_carpeta(ruta: Optional[str] = None) -> str:
    if ruta and os.path.isdir(ruta):
        return os.path.normpath(ruta)
    try:
        from PySide6.QtWidgets import QFileDialog, QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        ruta_seleccionada = QFileDialog.getExistingDirectory(
            None,
            "Seleccionar carpeta de trabajo",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        return os.path.normpath(ruta_seleccionada) if ruta_seleccionada else None
    except Exception as e:
        print(f"❌ Error al abrir explorador: {e}")
        return None


# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    # CRÍTICO: Protección necesaria para multiprocessing en Windows (spawn)
    # Sin esto, cada subproceso intentaría crear más subprocesos infinitamente
    import multiprocessing
    import sys
    
    # FREEZE_SUPPORT: Esencial para PyInstaller
    multiprocessing.freeze_support()
    
    # Detectar si estamos en entorno empaquetado (frozen)
    if getattr(sys, 'frozen', False):
        # Modo PyInstaller: configurar multiprocessing para entorno frozen
        multiprocessing.set_start_method('spawn', force=True)
    
    ruta_trabajo = obtener_ruta_carpeta()
    if ruta_trabajo:
        timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
        nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
        ruta_excel = os.path.join(ruta_trabajo, nombre_excel)
        procesar_diagnostico_a_excel(ruta_trabajo, ruta_excel, progress_callback=None)
    else:
        print("⛔ No se seleccionó carpeta. Operación cancelada.")