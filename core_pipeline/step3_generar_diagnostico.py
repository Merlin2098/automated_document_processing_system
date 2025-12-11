"""
Flujo combinado: Extracción de PDFs y generación directa de Excel
"""

import os
import sys
import time
from typing import List, Dict, Optional
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
# FUNCIONES DE PROCESAMIENTO
# ============================================

def procesar_carpeta(ruta_carpeta: str, config: Dict) -> List[Dict]:
    """
    Procesa todos los PDFs en una carpeta y genera registros.
    Si no hay extractor, solo lista archivos ordenados numéricamente.
    Progreso mostrado por lotes según BATCH_SIZE.
    """
    import re
    inicio = time.time()
    registros = []
    tipo_documento = config["tipo"]
    extractor = config.get("extractor")

    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.pdf')]
    
    # Ordenar archivos numéricamente por el número después del guión bajo
    def extraer_numero(filename):
        """Extrae el número del nombre de archivo para ordenamiento correcto"""
        match = re.search(r'_(\d+)', filename)
        return int(match.group(1)) if match else 0
    
    archivos_pdf.sort(key=extraer_numero)

    print(f"\n📂 Procesando carpeta: {os.path.basename(ruta_carpeta)}")
    logger.info(f"📂 Procesando carpeta: {os.path.basename(ruta_carpeta)}")
    print(f"   Tipo de documento: {tipo_documento}")
    logger.info(f"   Tipo: {tipo_documento}")
    print(f"   Total de PDFs encontrados: {len(archivos_pdf)}")
    logger.info(f"   PDFs: {len(archivos_pdf)}")

    # Si no hay extractor, solo listar archivos
    if extractor is None:
        for idx, archivo in enumerate(archivos_pdf, 1):
            registro = {
                "archivo": archivo
            }
            registros.append(registro)
            
            # Mostrar progreso cada BATCH_SIZE archivos
            if idx % BATCH_SIZE == 0:
                print(f"   Listados: {idx}/{len(archivos_pdf)}")
                logger.info(f"   Listados: {idx}/{len(archivos_pdf)}")
        
        fin = time.time()
        tiempo_total = fin - inicio
        print(f"   ✅ Completado: {len(registros)} archivos listados en {int(tiempo_total // 60)}m {int(tiempo_total % 60)}s")
        logger.info(f"   ✅ Completado: {len(registros)} archivos listados en {int(tiempo_total // 60)}m {int(tiempo_total % 60)}s")
        
        return registros

    # Si hay extractor, procesar normalmente con extracción de datos
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

        registros.append(registro)

        # Mostrar progreso cada BATCH_SIZE archivos
        if idx % BATCH_SIZE == 0:
            print(f"   Procesados: {idx}/{len(archivos_pdf)}")
            logger.info(f"   Procesados: {idx}/{len(archivos_pdf)}")

    fin = time.time()
    tiempo_total = fin - inicio
    print(f"   ✅ Completado: {len(registros)} registros en {int(tiempo_total // 60)}m {int(tiempo_total % 60)}s")
    logger.info(f"   ✅ Completado: {len(registros)} registros en {int(tiempo_total // 60)}m {int(tiempo_total % 60)}s")

    return registros


def escribir_parquet(registros: List[Dict], ruta_parquet: str) -> bool:
    """
    Escribe registros a archivo Parquet para procesamiento incremental.
    """
    try:
        import pandas as pd
        
        if not registros:
            logger.warning(f"No hay registros para escribir en {ruta_parquet}")
            return False
        
        df = pd.DataFrame(registros)
        df.to_parquet(ruta_parquet, engine='pyarrow', compression='snappy', index=False)
        
        logger.info(f"   💾 Parquet escrito: {os.path.basename(ruta_parquet)}")
        return True
        
    except ImportError:
        logger.error("pyarrow no está instalado. Instale con: pip install pyarrow")
        return False
    except Exception as e:
        logger.error(f"Error escribiendo Parquet: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ============================================
# FUNCIONES DE EXCEL
# ============================================

def generar_excel_desde_parquets(rutas_parquet: Dict[str, str], ruta_excel: str) -> bool:
    """
    Genera Excel con múltiples hojas desde archivos Parquet.
    Optimizado con DuckDB y dataframe_to_rows para máximo rendimiento.
    """
    try:
        import duckdb
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils.dataframe import dataframe_to_rows

        # Crear workbook
        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        for nombre_carpeta, ruta_parquet in rutas_parquet.items():
            # Leer Parquet con DuckDB (más rápido que pandas)
            if not os.path.exists(ruta_parquet):
                logger.warning(f"Archivo Parquet no encontrado: {ruta_parquet}")
                continue
            
            df = duckdb.read_parquet(ruta_parquet).df()
            
            if df.empty:
                logger.warning(f"DataFrame vacío para {nombre_carpeta}")
                continue
            
            # Obtener nombre de hoja personalizado del config
            config = CARPETAS_CONFIG.get(nombre_carpeta, {})
            nombre_hoja = config.get("nombre_hoja", nombre_carpeta)
            
            ws = wb.create_sheet(title=nombre_hoja)
            
            # Detectar si es una hoja de solo listado
            es_listado_simple = len(df.columns) == 1 and "archivo" in df.columns
            
            # Escribir encabezados con formato
            for col_idx, col_name in enumerate(df.columns, 1):
                cell = ws.cell(row=1, column=col_idx)
                if es_listado_simple:
                    cell.value = "ARCHIVO"
                else:
                    cell.value = col_name.replace("_", " ").upper()
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Escribir datos usando dataframe_to_rows (más rápido)
            for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 2):
                for c_idx, value in enumerate(row, 1):
                    ws.cell(row=r_idx, column=c_idx, value=value)
            
            # Ajustar anchos de columna
            for col_idx, col_name in enumerate(df.columns, 1):
                column_letter = openpyxl.utils.get_column_letter(col_idx)
                
                if es_listado_simple:
                    ws.column_dimensions[column_letter].width = 40
                else:
                    if col_name == "archivo_original":
                        ws.column_dimensions[column_letter].width = 40
                    elif col_name == "nombre_extraido":
                        ws.column_dimensions[column_letter].width = 30
                    elif col_name == "tipo_documento":
                        ws.column_dimensions[column_letter].width = 15
                    elif col_name == "dni_extraido":
                        ws.column_dimensions[column_letter].width = 12
                    elif col_name == "fecha_extraida":
                        ws.column_dimensions[column_letter].width = 15
                    else:
                        ws.column_dimensions[column_letter].width = 20
            
            ws.freeze_panes = "A2"
            
            logger.info(f"   ✅ Hoja '{nombre_hoja}' agregada al Excel ({len(df)} registros)")

        wb.save(ruta_excel)
        print(f"   ✅ Excel generado: {ruta_excel}")
        logger.info(f"   ✅ Excel generado: {ruta_excel}")
        return True

    except ImportError as e:
        print(f"   ❌ Dependencia faltante: {e}")
        logger.error(f"   ❌ Dependencia faltante: {e}")
        logger.error("   Instale con: pip install duckdb")
        return False
    except Exception as e:
        print(f"   ❌ Error al generar Excel: {e}")
        logger.error(f"   ❌ Error al generar Excel: {e}")
        import traceback
        traceback.print_exc()
        logger.error(traceback.format_exc())
        return False

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def procesar_diagnostico_a_excel(ruta_carpeta_trabajo: str, ruta_excel_final: str, guardar_json_opcional: bool = False):
    """
    Procesa PDFs y genera Excel usando Parquet como formato intermedio.
    Escritura incremental para mejor rendimiento y menor uso de memoria.
    Los archivos Parquet se guardan en la carpeta de trabajo con el mismo nombre base que el Excel.
    """
    print("="*60)
    print("🚀 PROCESO DE DIAGNÓSTICO CON PARQUET INCREMENTAL")
    print("="*60)
    logger.info("="*60)
    logger.info("🚀 PROCESO DE DIAGNÓSTICO CON PARQUET INCREMENTAL")
    logger.info("="*60)

    if not os.path.isdir(ruta_carpeta_trabajo):
        print(f"❌ Carpeta '{ruta_carpeta_trabajo}' no existe")
        logger.error(f"❌ Carpeta '{ruta_carpeta_trabajo}' no existe")
        return
    
    # Extraer nombre base del Excel (sin extensión)
    nombre_base_excel = os.path.splitext(os.path.basename(ruta_excel_final))[0]
    
    rutas_parquet = {}

    for nombre_carpeta, config in CARPETAS_CONFIG.items():
        ruta_subcarpeta = os.path.join(ruta_carpeta_trabajo, nombre_carpeta)
        if not os.path.isdir(ruta_subcarpeta):
            print(f"⚠️ Carpeta '{nombre_carpeta}' no encontrada, omitiendo...")
            logger.warning(f"⚠️ Carpeta '{nombre_carpeta}' no encontrada, omitiendo...")
            continue

        # Procesar carpeta
        registros = procesar_carpeta(ruta_subcarpeta, config)
        
        # Escribir Parquet con el mismo nombre base que el Excel
        nombre_parquet = f"{nombre_base_excel}_{nombre_carpeta}.parquet"
        ruta_parquet = os.path.join(ruta_carpeta_trabajo, nombre_parquet)
        if escribir_parquet(registros, ruta_parquet):
            rutas_parquet[nombre_carpeta] = ruta_parquet
        
        # Opcional: Guardar JSON para debugging
        if guardar_json_opcional and registros:
            import json
            ruta_json = os.path.join(ruta_carpeta_trabajo, f"diagnostico_{nombre_carpeta}.json")
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
            print(f"   💾 JSON opcional guardado: {ruta_json}")
            logger.info(f"   💾 JSON opcional guardado: {ruta_json}")
        
        # Liberar memoria
        del registros

    # Generar Excel desde Parquets
    if rutas_parquet:
        print("\n📊 Generando Excel desde archivos Parquet...")
        logger.info("📊 Generando Excel desde archivos Parquet...")
        generar_excel_desde_parquets(rutas_parquet, ruta_excel_final)
        
        print("\n✅ Proceso completado. Los archivos .parquet pueden ser eliminados manualmente.")
        logger.info("✅ Archivos .parquet guardados en carpeta de trabajo (pueden eliminarse)")

# ============================================
# OBTENER RUTA DE CARPETA
# ============================================

def obtener_ruta_carpeta(ruta: Optional[str] = None) -> str:
    if ruta and os.path.isdir(ruta):
        return os.path.normpath(ruta)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        ruta_seleccionada = filedialog.askdirectory(title="Seleccionar carpeta de trabajo", mustexist=True)
        root.destroy()
        return os.path.normpath(ruta_seleccionada) if ruta_seleccionada else None
    except Exception as e:
        print(f"❌ Error al abrir explorador: {e}")
        return None

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    ruta_trabajo = obtener_ruta_carpeta()
    if ruta_trabajo:
        # Generar timestamp para el nombre del archivo
        timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
        nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
        ruta_excel = os.path.join(ruta_trabajo, nombre_excel)
        procesar_diagnostico_a_excel(ruta_trabajo, ruta_excel, guardar_json_opcional=False)
    else:
        print("⛔ No se seleccionó carpeta. Operación cancelada.")