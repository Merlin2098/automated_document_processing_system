"""
Worker para generar diagnóstico de datos (Paso 3) - OPTIMIZADO
Soporta multiprocessing con progreso global por carpeta
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time

# Agregar ruta del módulo core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_pipeline.step3_generar_diagnostico import (
    procesar_diagnostico_a_excel,
    CARPETAS_CONFIG
)


def format_time(seconds: float) -> str:
    """Convierte segundos a formato hh:mm:ss"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def contar_archivos_totales(folder_path: str) -> dict:
    """
    Cuenta el total de archivos PDF en todas las carpetas a procesar.
    Returns: {'total': int, 'por_carpeta': {nombre_carpeta: count}}
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
    """Worker optimizado para generar diagnóstico en segundo plano con multiprocessing"""
    
    # Señales (compatible con UI existente)
    progress_signal = Signal(int, int)  # (current, total) - archivos procesados
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas detalladas
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    def __init__(self, folder_path: str, guardar_json: bool = False):
        super().__init__()
        self.folder_path = folder_path
        self.guardar_json = guardar_json
        self._is_running = True
        self.logger = Logger("CorePipelineStep3Worker")
        
        # Contadores para estadísticas
        self.archivos_totales = 0
        self.archivos_procesados = 0
        self.carpetas_totales = 0
        self.carpetas_procesadas = 0
        self.errores_acumulados = 0
    
    def run(self):
        """Ejecuta el proceso de generación de diagnóstico optimizado"""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Worker: Iniciando diagnóstico optimizado")
            self.log_signal.emit("info", "🚀 Iniciando generación de diagnóstico (modo paralelo)...")
            
            # Contar archivos totales antes de iniciar
            conteo = contar_archivos_totales(self.folder_path)
            self.archivos_totales = conteo['total']
            self.carpetas_totales = len([c for c in CARPETAS_CONFIG.keys() 
                                        if os.path.isdir(os.path.join(self.folder_path, c))])
            
            if self.carpetas_totales == 0:
                self.error_signal.emit("No se encontraron carpetas válidas para procesar")
                self.logger.error("❌ Sin carpetas válidas")
                return
            
            self.logger.info(f"📂 Total: {self.archivos_totales} archivos en {self.carpetas_totales} carpetas")
            self.log_signal.emit("info", f"📂 Total: {self.archivos_totales} archivos en {self.carpetas_totales} carpetas")
            
            # Emitir estadísticas iniciales
            self._emit_stats(start_time)
            
            # Generar nombre de Excel con timestamp
            timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
            nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
            ruta_excel = os.path.join(self.folder_path, nombre_excel)
            
            # Callback para actualizar progreso desde el core multiproceso
            def _progress_callback(carpetas_completadas, total_carpetas, tiempo_carpeta, logs=None):
                if not self._is_running:
                    return

                self.carpetas_procesadas = carpetas_completadas

                # Estimar archivos procesados basado en carpetas completadas
                # (aproximación: archivos procesados = proporción de carpetas * total archivos)
                proporcion = carpetas_completadas / total_carpetas if total_carpetas > 0 else 0
                self.archivos_procesados = int(self.archivos_totales * proporcion)

                # Emitir progreso de archivos (aproximado durante multiprocessing)
                self.progress_signal.emit(self.archivos_procesados, self.archivos_totales)

                # Surfacear errores y resúmenes de extracción al UI
                if logs:
                    for log_line in logs:
                        if "⚠️ Fallo extracción:" in log_line:
                            self.errores_acumulados += 1
                            self.log_signal.emit("warning", log_line.strip())
                        elif "📊 Resumen:" in log_line:
                            self.log_signal.emit("info", log_line.strip())

                # Emitir estadísticas actualizadas
                self._emit_stats(start_time)

                # Log de progreso
                tiempo_fmt = format_time(time.time() - start_time)
                self.logger.info(f"📊 Progreso: {carpetas_completadas}/{total_carpetas} carpetas | {tiempo_fmt}")
                self.log_signal.emit("info", f"📊 Carpeta {carpetas_completadas}/{total_carpetas} completada en {int(tiempo_carpeta)}s")
            
            # Ejecutar procesamiento con callback
            procesar_diagnostico_a_excel(
                ruta_carpeta_trabajo=self.folder_path,
                ruta_excel_final=ruta_excel,
                progress_callback=_progress_callback,
                guardar_json_opcional=self.guardar_json
            )
            
            # Verificar que el Excel se generó
            if not os.path.exists(ruta_excel):
                self.error_signal.emit("El archivo Excel no se generó correctamente")
                self.logger.error("❌ Excel no generado")
                return
            
            # Actualizar a 100% al finalizar
            self.archivos_procesados = self.archivos_totales
            self.carpetas_procesadas = self.carpetas_totales
            self.progress_signal.emit(self.archivos_totales, self.archivos_totales)
            
            # Tiempo total
            elapsed_time = time.time() - start_time
            time_formatted = format_time(elapsed_time)
            
            # Emitir estadísticas finales
            stats_final = {
                'current': self.archivos_totales,
                'total': self.archivos_totales,
                'time_elapsed': time_formatted,
                'carpetas_procesadas': self.carpetas_totales,
                'total_carpetas': self.carpetas_totales,
                'errors': self.errores_acumulados,
                'ruta_excel': ruta_excel
            }
            self.stats_signal.emit(stats_final)
            
            # Resultado exitoso
            resultado = {
                'success': True,
                'excel_path': ruta_excel,
                'stats': stats_final,
                'carpetas_procesadas': self.carpetas_totales,
                'archivos_procesados': self.archivos_totales
            }
            
            self.logger.info(f"✅ Worker completado en {time_formatted}")
            self.log_signal.emit("success", f"✅ Diagnóstico generado exitosamente en {time_formatted}")
            self.finished_signal.emit(resultado)
            
        except Exception as e:
            import traceback
            error_msg = f"Error en worker: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
            self.finished_signal.emit({'success': False, 'error': str(e)})
    
    def _emit_stats(self, start_time: float):
        """Emite estadísticas actuales (compatible con UI)"""
        elapsed_time = time.time() - start_time
        time_formatted = format_time(elapsed_time)
        
        stats = {
            'current': self.archivos_procesados,
            'total': self.archivos_totales,
            'time_elapsed': time_formatted,
            'carpetas_procesadas': self.carpetas_procesadas,
            'total_carpetas': self.carpetas_totales,
            'errors': self.errores_acumulados
        }
        self.stats_signal.emit(stats)
    
    def stop(self):
        """Detener el worker (multiprocessing no permite stop fácil, pero marcamos flag)"""
        self.logger.warning("⚠️ Solicitud de detención recibida")
        self._is_running = False
        self.quit()