"""
Worker para renombrar archivos (Paso 4) - VERSIÓN MEJORADA CON PARALELIZACIÓN
Usa procesamiento paralelo y señales enriquecidas para mejor UX
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Agregar rutas para imports del core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar funciones PURAS del core (sin dependencias de UI)
from core_pipeline.step4_rename import (
    cargar_json,
    convertir_json_a_mapeo,
    renombrar_archivos
)


class CorePipelineStep4Worker(QThread):
    """Worker wrapper para renombrar archivos con procesamiento paralelo"""
    
    # Señales básicas
    progress_signal = Signal(int, int)  # (current, total) - carpetas procesadas
    log_signal = Signal(str, str)  # (type, message)
    stats_signal = Signal(dict)  # estadísticas finales
    finished_signal = Signal(dict)  # resultado final
    error_signal = Signal(str)  # mensaje de error
    
    # Señales enriquecidas (NUEVAS)
    time_update_signal = Signal(float)  # segundos transcurridos
    file_progress_signal = Signal(int, int)  # (archivos procesados, total archivos)
    folder_update_signal = Signal(str)  # nombre carpeta actual
    overall_progress_signal = Signal(int)  # progreso global 0-100
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        self.logger = Logger("CorePipelineStep4Worker")
        
        # Carpetas a procesar
        self.carpetas_a_procesar = ['1_Boletas', '2_Afp', '3_5ta', '4_Convocatoria', '5_CertificadosTrabajo']
        
        # Control de progreso
        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.files_lock = Lock()  # Para thread-safety
        
        # Resultados acumulados
        self.estadisticas = []
        self.stats_lock = Lock()
    
    def run(self):
        """Ejecuta el proceso usando funciones del core con paralelización"""
        try:
            self.start_time = time.time()
            
            self.logger.info("🚀 Iniciando renombrado de archivos (modo paralelo)")
            self.log_signal.emit("info", "🚀 Iniciando renombrado de archivos (modo paralelo)")
            self.logger.info(f"📂 Carpeta madre: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta madre: {self.folder_path}")
            
            # Validar carpeta
            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return
            
            # ============================================================
            # FASE 1: Escanear carpetas y contar archivos totales
            # ============================================================
            self.log_signal.emit("info", "📊 Escaneando carpetas...")
            self.logger.info("📊 Escaneando carpetas...")
            
            carpetas_validas = []
            for nombre_carpeta in self.carpetas_a_procesar:
                if not self._is_running:
                    return
                
                ruta_lote = os.path.join(self.folder_path, nombre_carpeta)
                
                if not os.path.exists(ruta_lote) or not os.path.isdir(ruta_lote):
                    continue
                
                # Buscar JSON
                archivos_json = [f for f in os.listdir(ruta_lote) if f.endswith('.json')]
                if not archivos_json:
                    continue
                
                # Cargar y contar archivos
                ruta_json = os.path.join(ruta_lote, archivos_json[0])
                datos_json = cargar_json(ruta_json)
                
                if datos_json and isinstance(datos_json, list):
                    mapeo = convertir_json_a_mapeo(datos_json)
                    if mapeo:
                        file_count = len(mapeo)
                        self.total_files += file_count
                        carpetas_validas.append((nombre_carpeta, ruta_lote, file_count))
                        
                        msg = f"   📁 {nombre_carpeta}: {file_count} archivos"
                        self.log_signal.emit("info", msg)
                        self.logger.info(msg)
            
            if not carpetas_validas:
                msg = "⚠️ No se encontraron carpetas válidas con JSONs para procesar"
                self.log_signal.emit("warning", msg)
                self.logger.warning(msg)
                self._finish_with_results()
                return
            
            msg = f"📊 Total a procesar: {self.total_files} archivos en {len(carpetas_validas)} carpetas"
            self.log_signal.emit("info", msg)
            self.logger.info(msg)
            
            # Inicializar progreso
            self.file_progress_signal.emit(0, self.total_files)
            self.overall_progress_signal.emit(0)
            
            # ============================================================
            # FASE 2: Procesamiento paralelo de carpetas
            # ============================================================
            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "🔄 Iniciando procesamiento paralelo...")
            self.logger.info("🔄 Iniciando procesamiento paralelo...")
            
            # Usar ThreadPoolExecutor para paralelizar
            max_workers = min(len(carpetas_validas), 5)  # Máximo 5 threads
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar todas las carpetas a procesar
                future_to_carpeta = {
                    executor.submit(self._procesar_lote_paralelo, nombre, ruta): nombre
                    for nombre, ruta, _ in carpetas_validas
                }
                
                # Procesar resultados conforme se completan
                carpetas_completadas = 0
                for future in as_completed(future_to_carpeta):
                    if not self._is_running:
                        executor.shutdown(wait=False, cancel_futures=True)
                        return
                    
                    nombre_carpeta = future_to_carpeta[future]
                    
                    try:
                        resultado = future.result()
                        
                        # Agregar a estadísticas de forma thread-safe
                        with self.stats_lock:
                            self.estadisticas.append(resultado)
                        
                        carpetas_completadas += 1
                        
                        # Emitir progreso de carpetas
                        self.progress_signal.emit(carpetas_completadas, len(carpetas_validas))
                        
                        # Mostrar resultado
                        if resultado['estado'] == 'procesado':
                            msg = f"   ✅ {nombre_carpeta}: {resultado['exitosos']} renombrados | {resultado['omitidos']} omitidos | {resultado['fallidos']} errores"
                            self.log_signal.emit("success", msg)
                            self.logger.info(msg)
                        else:
                            msg = f"   ⚠️ {nombre_carpeta}: {resultado['estado']}"
                            self.log_signal.emit("warning", msg)
                            self.logger.warning(msg)
                        
                        # Actualizar tiempo
                        elapsed = time.time() - self.start_time
                        self.time_update_signal.emit(elapsed)
                        
                    except Exception as e:
                        self.logger.error(f"Error procesando {nombre_carpeta}: {str(e)}")
                        self.log_signal.emit("error", f"❌ Error en {nombre_carpeta}: {str(e)}")
            
            # ============================================================
            # FASE 3: Resumen final
            # ============================================================
            self._finish_with_results()
            
        except Exception as e:
            error_msg = f"Error durante el proceso: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
    
    def _procesar_lote_paralelo(self, nombre_lote: str, carpeta_lote: str) -> dict:
        """
        Procesa un lote (carpeta) en paralelo usando funciones del core.
        Esta función se ejecuta en un thread separado.
        
        Returns:
            dict: Estadísticas del procesamiento
        """
        try:
            # Notificar carpeta actual
            self.folder_update_signal.emit(nombre_lote)
            
            # Buscar archivo JSON
            archivos_json = [f for f in os.listdir(carpeta_lote) if f.endswith('.json')]
            
            if not archivos_json:
                self.logger.warning(f"   ⚠️ No se encontró archivo JSON en {nombre_lote}")
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'sin_json'
                }
            
            ruta_json = os.path.join(carpeta_lote, archivos_json[0])
            
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
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'json_vacio'
                }
            
            # Convertir a mapeo
            mapeo = convertir_json_a_mapeo(datos_json)
            
            if not mapeo:
                return {
                    'lote': nombre_lote,
                    'exitosos': 0,
                    'fallidos': 0,
                    'omitidos': 0,
                    'total': 0,
                    'estado': 'mapeo_vacio'
                }
            
            # Ejecutar renombrado
            exitosos, fallidos, omitidos, total = renombrar_archivos(carpeta_lote, mapeo)
            
            # Actualizar progreso de archivos de forma thread-safe
            with self.files_lock:
                self.processed_files += total
                progress_percent = int((self.processed_files / self.total_files) * 100) if self.total_files > 0 else 0
                
                # Emitir señales
                self.file_progress_signal.emit(self.processed_files, self.total_files)
                self.overall_progress_signal.emit(progress_percent)
            
            return {
                'lote': nombre_lote,
                'exitosos': exitosos,
                'fallidos': fallidos,
                'omitidos': omitidos,
                'total': total,
                'estado': 'procesado'
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando lote {nombre_lote}: {str(e)}")
            return {
                'lote': nombre_lote,
                'exitosos': 0,
                'fallidos': 0,
                'omitidos': 0,
                'total': 0,
                'estado': 'error'
            }
    
    def _finish_with_results(self):
        """Finaliza el proceso y emite resultados"""
        # Calcular totales
        total_exitosos = sum(e['exitosos'] for e in self.estadisticas)
        total_fallidos = sum(e['fallidos'] for e in self.estadisticas)
        total_omitidos = sum(e['omitidos'] for e in self.estadisticas)
        total_archivos = sum(e['total'] for e in self.estadisticas)
        
        # Tiempo total
        elapsed = time.time() - self.start_time
        self.time_update_signal.emit(elapsed)
        
        # Logs finales
        self.log_signal.emit("info", "")
        self.log_signal.emit("info", "=" * 50)
        self.log_signal.emit("info", "📊 RESUMEN FINAL")
        self.log_signal.emit("info", f"📂 Lotes procesados: {len(self.estadisticas)}")
        self.log_signal.emit("success", f"✅ Archivos renombrados: {total_exitosos}")
        self.log_signal.emit("info", f"⊘ Archivos omitidos: {total_omitidos}")
        
        if total_fallidos > 0:
            self.log_signal.emit("error", f"❌ Archivos con errores: {total_fallidos}")
        
        if total_archivos > 0:
            porcentaje = (total_exitosos / total_archivos) * 100
            self.log_signal.emit("info", f"📊 Tasa de éxito: {porcentaje:.1f}%")
        
        # Tiempo
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self.log_signal.emit("info", f"⏱️ Tiempo total: {mins}m {secs}s")
        self.log_signal.emit("info", "=" * 50)
        
        # Log a archivo
        self.logger.info("=" * 50)
        self.logger.info("📊 RESUMEN FINAL")
        self.logger.info(f"📂 Lotes procesados: {len(self.estadisticas)}")
        self.logger.info(f"✅ Archivos renombrados: {total_exitosos}")
        self.logger.info(f"⊘ Archivos omitidos: {total_omitidos}")
        
        if total_fallidos > 0:
            self.logger.error(f"❌ Archivos con errores: {total_fallidos}")
        
        if total_archivos > 0:
            porcentaje = (total_exitosos / total_archivos) * 100
            self.logger.info(f"📊 Tasa de éxito: {porcentaje:.1f}%")
        
        self.logger.info(f"⏱️ Tiempo total: {mins}m {secs}s")
        self.logger.info("=" * 50)
        
        # Emitir estadísticas
        stats = {
            'lotes_procesados': len(self.estadisticas),
            'total_exitosos': total_exitosos,
            'total_fallidos': total_fallidos,
            'total_omitidos': total_omitidos,
            'total_archivos': total_archivos,
            'tiempo_transcurrido': elapsed,
            'detalle_por_lote': self.estadisticas
        }
        self.stats_signal.emit(stats)
        
        # Emitir resultado final
        resultado = {
            'success': True,
            'stats': stats
        }
        
        self.logger.info("🎉 ¡Renombrado completado exitosamente!")
        self.log_signal.emit("success", "🎉 ¡Renombrado completado exitosamente!")
        
        # Progreso final
        self.overall_progress_signal.emit(100)
        
        self.finished_signal.emit(resultado)
    
    def stop(self):
        """Detiene el worker"""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")