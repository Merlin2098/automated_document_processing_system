"""
Worker para generar diagnóstico (Paso 3) - WRAPPER PATTERN
Usa directamente las funciones del módulo core sin reimplementar lógica
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time

# Agregar rutas para imports del core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar funciones PURAS del core (sin dependencias de UI)
from core_pipeline.step3_generar_diagnostico import (
    procesar_carpeta,
    escribir_parquet,
    generar_excel_desde_parquets,
    CARPETAS_CONFIG,
    BATCH_SIZE
)


def format_time(seconds: float) -> str:
    """
    Convierte segundos a formato hh:mm:ss
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def contar_archivos_totales(folder_path: str) -> dict:
    """
    Cuenta el total de archivos PDF en todas las carpetas a procesar.
    
    Returns:
        dict: {'total': int, 'por_carpeta': {nombre_carpeta: count}}
    """
    total = 0
    por_carpeta = {}
    
    for nombre_carpeta in CARPETAS_CONFIG.keys():
        ruta_subcarpeta = os.path.join(folder_path, nombre_carpeta)
        if os.path.isdir(ruta_subcarpeta):
            archivos_pdf = [f for f in os.listdir(ruta_subcarpeta) if f.lower().endswith('.pdf')]
            count = len(archivos_pdf)
            por_carpeta[nombre_carpeta] = count
            total += count
    
    return {'total': total, 'por_carpeta': por_carpeta}


class CorePipelineStep3Worker(QThread):
    """Worker wrapper para generar diagnóstico Excel"""
    
    # Señales
    progress_signal = Signal(int, int)  # (current, total)
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str, guardar_json: bool = False):
        super().__init__()
        self.folder_path = folder_path
        self.guardar_json = guardar_json
        self._is_running = True
        self.logger = Logger("CorePipelineStep3Worker")
    
    def run(self):
        """Ejecuta el proceso usando funciones del core"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Iniciando generación de diagnóstico")
            self.log_signal.emit("info", "🚀 Iniciando generación de diagnóstico")
            self.logger.info(f"📂 Carpeta de trabajo: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta de trabajo: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Verificar openpyxl
            try:
                import openpyxl
            except ImportError:
                error_msg = "openpyxl no está instalado. Instale con: pip install openpyxl"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # Generar timestamp para el Excel
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
            nombre_base_excel = f"diagnostico_consolidado_{timestamp}"
            ruta_excel = os.path.join(self.folder_path, nombre_excel)
            
            self.log_signal.emit("info", f"📊 Excel: {nombre_excel}")
            self.logger.info(f"📊 Excel: {nombre_excel}")
            
            # ============================================================
            # FASE 0: Contar archivos totales
            # ============================================================
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 Contando archivos a procesar...")
            self.logger.info("📋 Contando archivos a procesar...")
            
            conteo = contar_archivos_totales(self.folder_path)
            total_archivos_global = conteo['total']
            archivos_por_carpeta = conteo['por_carpeta']
            
            if total_archivos_global == 0:
                error_msg = "No se encontraron archivos PDF para procesar"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            self.log_signal.emit("info", f"✅ Total de archivos a procesar: {total_archivos_global}")
            self.logger.info(f"✅ Total de archivos: {total_archivos_global}")
            
            # Emitir progreso inicial
            self.progress_signal.emit(0, total_archivos_global)
            
            # ============================================================
            # FASE 1-3: Procesar cada carpeta (USA EL CORE)
            # ============================================================
            rutas_parquet = {}
            total_carpetas = len(CARPETAS_CONFIG)
            carpetas_procesadas = 0
            archivos_procesados_global = 0
            total_registros = 0
            errores_acumulados = 0
            
            for nombre_carpeta, config in CARPETAS_CONFIG.items():
                if not self._is_running:
                    self.logger.warning("Proceso cancelado por el usuario")
                    return
                
                ruta_subcarpeta = os.path.join(self.folder_path, nombre_carpeta)
                
                if not os.path.isdir(ruta_subcarpeta):
                    msg = f"⚠️ Carpeta '{nombre_carpeta}' no encontrada, omitiendo..."
                    self.log_signal.emit("warning", msg)
                    self.logger.warning(msg)
                    carpetas_procesadas += 1
                    continue
                
                self.log_signal.emit("info", "")
                msg = f"📋 Procesando: {nombre_carpeta} ({config['tipo']})"
                self.log_signal.emit("info", msg)
                self.logger.info(msg)
                
                # Obtener lista de archivos PDF
                archivos_pdf = [f for f in os.listdir(ruta_subcarpeta) if f.lower().endswith('.pdf')]
                
                # Ordenar archivos numéricamente
                import re
                def extraer_numero(filename):
                    match = re.search(r'_(\d+)', filename)
                    return int(match.group(1)) if match else 0
                archivos_pdf.sort(key=extraer_numero)
                
                tiene_extractor = config.get("extractor") is not None
                extractor = config.get("extractor")
                tipo_documento = config["tipo"]
                
                registros = []
                errores_en_carpeta = 0
                
                # Procesar archivos con progreso por lotes según BATCH_SIZE del core
                lote_actual = []
                
                for idx, archivo in enumerate(archivos_pdf, 1):
                    ruta_completa = os.path.join(ruta_subcarpeta, archivo)
                    
                    if extractor is None:
                        # Solo listado
                        registro = {"archivo": archivo}
                    else:
                        # Extracción de datos
                        resultado = extractor(ruta_completa)
                        registro = {
                            "archivo_original": archivo,
                            "tipo_documento": tipo_documento,
                            "nombre_extraido": resultado.get("nombre"),
                            "dni_extraido": resultado.get("dni")
                        }
                        if "fecha" in resultado and resultado["fecha"]:
                            registro["fecha_extraida"] = resultado["fecha"]
                        
                        # Contar errores
                        if not (resultado.get("nombre") or resultado.get("dni")):
                            errores_en_carpeta += 1
                    
                    registros.append(registro)
                    lote_actual.append(registro)
                    
                    # Emitir progreso cada BATCH_SIZE archivos o al final
                    if len(lote_actual) >= BATCH_SIZE or idx == len(archivos_pdf):
                        archivos_procesados_global += len(lote_actual)
                        errores_acumulados += errores_en_carpeta
                        
                        # Emitir progreso
                        self.progress_signal.emit(archivos_procesados_global, total_archivos_global)
                        
                        # Emitir estadísticas parciales
                        elapsed_time = time.time() - start_time
                        time_formatted = format_time(elapsed_time)
                        
                        stats_parciales = {
                            'current': archivos_procesados_global,
                            'total': total_archivos_global,
                            'time_elapsed': time_formatted,
                            'carpetas_procesadas': carpetas_procesadas,
                            'total_carpetas': total_carpetas,
                            'errors': errores_acumulados
                        }
                        self.stats_signal.emit(stats_parciales)
                        
                        # Limpiar lote
                        lote_actual = []
                
                # Actualizar contadores
                total_registros += len(registros)
                
                msg = f"   ✅ {len(registros)} registros generados"
                self.log_signal.emit("success", msg)
                self.logger.info(msg)
                
                # Escribir Parquet con el mismo nombre base que el Excel (USA EL CORE)
                nombre_parquet = f"{nombre_base_excel}_{nombre_carpeta}.parquet"
                ruta_parquet = os.path.join(self.folder_path, nombre_parquet)
                if escribir_parquet(registros, ruta_parquet):
                    rutas_parquet[nombre_carpeta] = ruta_parquet
                    self.log_signal.emit("info", f"   💾 Parquet guardado: {nombre_parquet}")
                
                # Guardar JSON opcional si se solicita
                if self.guardar_json and registros:
                    import json
                    ruta_json = os.path.join(self.folder_path, f"diagnostico_{nombre_carpeta}.json")
                    try:
                        with open(ruta_json, 'w', encoding='utf-8') as f:
                            json.dump(registros, f, ensure_ascii=False, indent=2)
                        msg = f"   💾 JSON guardado: {os.path.basename(ruta_json)}"
                        self.log_signal.emit("info", msg)
                        self.logger.info(msg)
                    except Exception as e:
                        self.logger.error(f"Error guardando JSON: {e}")
                
                # Liberar memoria
                del registros
                
                # Incrementar carpetas procesadas DESPUÉS de terminar la carpeta
                carpetas_procesadas += 1
                
                # Emitir tiempo transcurrido después de cada carpeta
                elapsed_time = time.time() - start_time
                time_formatted = format_time(elapsed_time)
                self.log_signal.emit("info", f"   ⏱️ Tiempo transcurrido: {time_formatted}")
                self.logger.info(f"   ⏱️ Tiempo transcurrido: {time_formatted}")
                
                # Emitir estadísticas con carpetas actualizadas
                stats_parciales = {
                    'current': archivos_procesados_global,
                    'total': total_archivos_global,
                    'time_elapsed': time_formatted,
                    'carpetas_procesadas': carpetas_procesadas,
                    'total_carpetas': total_carpetas,
                    'errors': errores_acumulados
                }
                self.stats_signal.emit(stats_parciales)
            
            # Verificar que haya datos para procesar
            if not rutas_parquet or archivos_procesados_global == 0:
                error_msg = "No se generaron registros. Verifique que las carpetas contengan PDFs válidos."
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # FASE 4: Generar Excel desde Parquets (USA EL CORE)
            # ============================================================
            if not self._is_running:
                self.logger.warning("Proceso cancelado por el usuario")
                return
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "📋 Generando archivo Excel desde Parquets...")
            self.logger.info("📋 Generando archivo Excel desde Parquets...")
            
            exito = generar_excel_desde_parquets(rutas_parquet, ruta_excel)
            
            if not exito:
                error_msg = "Error al generar el archivo Excel"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # FASE 5: Resumen final
            # ============================================================
            elapsed_time = time.time() - start_time
            time_formatted = format_time(elapsed_time)
            
            # Calcular estadísticas por tipo leyendo Parquets con DuckDB
            import duckdb
            stats_por_tipo = {}
            total_exitosos = 0
            total_fallidos = 0
            
            for nombre_carpeta, ruta_parquet in rutas_parquet.items():
                # Leer Parquet con DuckDB (más rápido que pandas)
                df = duckdb.read_parquet(ruta_parquet).df()
                
                # Obtener config de la carpeta
                config = CARPETAS_CONFIG.get(nombre_carpeta, {})
                tiene_extractor = config.get("extractor") is not None
                
                # Solo contar extracciones en carpetas que tienen extractor
                if tiene_extractor:
                    # Si tiene nombre_extraido o dni_extraido, se considera exitoso
                    exitosos = df[
                        (df.get('nombre_extraido', df.iloc[:, 0].map(lambda x: None)).notna()) | 
                        (df.get('dni_extraido', df.iloc[:, 0].map(lambda x: None)).notna())
                    ].shape[0]
                    fallidos = len(df) - exitosos
                    
                    stats_por_tipo[nombre_carpeta] = {
                        'total': len(df),
                        'exitosos': exitosos,
                        'fallidos': fallidos,
                        'tiene_extractor': True
                    }
                    
                    total_exitosos += exitosos
                    total_fallidos += fallidos
                else:
                    # Para carpetas sin extractor (solo listado)
                    stats_por_tipo[nombre_carpeta] = {
                        'total': len(df),
                        'exitosos': 0,
                        'fallidos': 0,
                        'tiene_extractor': False
                    }
            
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "=" * 50)
            self.log_signal.emit("info", "📊 RESUMEN FINAL")
            self.log_signal.emit("info", f"📂 Carpetas procesadas: {carpetas_procesadas}/{total_carpetas}")
            self.log_signal.emit("info", f"📄 Total archivos: {archivos_procesados_global}")
            self.log_signal.emit("success", f"✅ Extracciones exitosas: {total_exitosos}")
            
            if total_fallidos > 0:
                self.log_signal.emit("error", f"❌ Extracciones fallidas: {total_fallidos}")
                porcentaje_exito = (total_exitosos / archivos_procesados_global * 100) if archivos_procesados_global > 0 else 0
                self.log_signal.emit("info", f"📊 Tasa de éxito: {porcentaje_exito:.1f}%")
            
            self.log_signal.emit("info", f"📊 Excel generado: {nombre_excel}")
            self.log_signal.emit("info", f"⏱️ Tiempo total: {time_formatted}")
            self.log_signal.emit("info", "=" * 50)
            
            # Log a archivo
            self.logger.info("=" * 50)
            self.logger.info("📊 RESUMEN FINAL")
            self.logger.info(f"📂 Carpetas procesadas: {carpetas_procesadas}/{total_carpetas}")
            self.logger.info(f"📄 Total archivos: {archivos_procesados_global}")
            self.logger.info(f"✅ Extracciones exitosas: {total_exitosos}")
            
            if total_fallidos > 0:
                self.logger.error(f"❌ Extracciones fallidas: {total_fallidos}")
            
            self.logger.info(f"📊 Excel: {ruta_excel}")
            self.logger.info(f"⏱️ Tiempo: {time_formatted}")
            self.logger.info("=" * 50)
            
            # Emitir estadísticas finales
            stats = {
                'current': archivos_procesados_global,
                'total': total_archivos_global,
                'carpetas_procesadas': carpetas_procesadas,
                'total_carpetas': total_carpetas,
                'total_registros': archivos_procesados_global,
                'exitosos': total_exitosos,
                'fallidos': total_fallidos,
                'errors': total_fallidos,
                'stats_por_tipo': stats_por_tipo,
                'ruta_excel': ruta_excel,
                'time_elapsed': time_formatted
            }
            self.stats_signal.emit(stats)
            
            # Emitir resultado final
            resultado = {
                'success': True,
                'stats': stats,
                'excel_path': ruta_excel
            }
            
            self.logger.info("🎉 ¡Diagnóstico completado exitosamente!")
            self.log_signal.emit("success", "🎉 ¡Diagnóstico completado exitosamente!")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            error_msg = f"Error durante el proceso: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")