"""
Worker para renombrar archivos (Paso 4) - VERSION MEJORADA CON PARALELIZACION
Usa procesamiento paralelo y validacion previa estricta para mejor UX.
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

from core_pipeline.step4_rename import (
    EXPECTED_RENAME_FOLDERS,
    cargar_json,
    convertir_json_a_mapeo,
    renombrar_archivos,
    validar_preflight_renombrado,
)


class CorePipelineStep4Worker(QThread):
    """Worker wrapper para renombrar archivos con preflight y paralelizacion."""

    progress_signal = Signal(int, int)
    log_signal = Signal(str, str)
    stats_signal = Signal(dict)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    time_update_signal = Signal(float)
    file_progress_signal = Signal(int, int)
    folder_update_signal = Signal(str)
    overall_progress_signal = Signal(int)

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
        self.logger = Logger("CorePipelineStep4Worker")

        self.carpetas_a_procesar = list(EXPECTED_RENAME_FOLDERS)

        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.files_lock = Lock()

        self.estadisticas = []
        self.stats_lock = Lock()
        self.preflight_report = None

    def run(self):
        """Ejecuta el proceso usando validacion previa y funciones del core."""
        try:
            self.start_time = time.time()

            self.logger.info("🚀 Iniciando renombrado de archivos (modo paralelo)")
            self.log_signal.emit("info", "🚀 Iniciando renombrado de archivos (modo paralelo)")
            self.logger.info(f"📂 Carpeta madre: {self.folder_path}")
            self.log_signal.emit("info", f"📂 Carpeta madre: {self.folder_path}")

            if not os.path.isdir(self.folder_path):
                error_msg = f"La carpeta no existe: {self.folder_path}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return

            self.log_signal.emit("info", "🔎 Ejecutando validacion previa del renombrado...")
            self.logger.info("🔎 Ejecutando validacion previa del renombrado...")

            self.preflight_report = validar_preflight_renombrado(
                self.folder_path,
                self.carpetas_a_procesar,
            )

            if not self.preflight_report.get('preflight_ok'):
                self._handle_preflight_failure(self.preflight_report)
                return

            carpetas_validas = []
            for detalle in self.preflight_report.get('folders_ready', []):
                carpetas_validas.append(
                    (
                        detalle['folder_name'],
                        detalle['folder_path'],
                        detalle['selected_json_path'],
                        detalle.get('mapping_count', 0),
                    )
                )

            self.total_files = sum(file_count for _, _, _, file_count in carpetas_validas)

            for nombre_carpeta, _, _, file_count in carpetas_validas:
                msg = f"   📁 {nombre_carpeta}: {file_count} archivos validados"
                self.log_signal.emit("info", msg)
                self.logger.info(msg)

            msg = f"📊 Total a procesar: {self.total_files} archivos en {len(carpetas_validas)} carpetas"
            self.log_signal.emit("info", msg)
            self.logger.info(msg)

            self.file_progress_signal.emit(0, self.total_files)
            self.overall_progress_signal.emit(0)

            self.log_signal.emit("info", "")
            self.log_signal.emit("info", "🔄 Iniciando procesamiento paralelo...")
            self.logger.info("🔄 Iniciando procesamiento paralelo...")

            max_workers = min(len(carpetas_validas), 5) if carpetas_validas else 1

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_carpeta = {
                    executor.submit(self._procesar_lote_paralelo, nombre, ruta, ruta_json): nombre
                    for nombre, ruta, ruta_json, _ in carpetas_validas
                }

                carpetas_completadas = 0
                for future in as_completed(future_to_carpeta):
                    if not self._is_running:
                        executor.shutdown(wait=False, cancel_futures=True)
                        return

                    nombre_carpeta = future_to_carpeta[future]

                    try:
                        resultado = future.result()

                        with self.stats_lock:
                            self.estadisticas.append(resultado)

                        carpetas_completadas += 1
                        self.progress_signal.emit(carpetas_completadas, len(carpetas_validas))

                        if resultado['estado'] == 'procesado':
                            msg = f"   ✅ {nombre_carpeta}: {resultado['exitosos']} renombrados | {resultado['omitidos']} omitidos | {resultado['fallidos']} errores"
                            self.log_signal.emit("success", msg)
                            self.logger.info(msg)
                        else:
                            msg = f"   ⚠️ {nombre_carpeta}: {resultado['estado']}"
                            self.log_signal.emit("warning", msg)
                            self.logger.warning(msg)

                        elapsed = time.time() - self.start_time
                        self.time_update_signal.emit(elapsed)

                    except Exception as e:
                        self.logger.error(f"Error procesando {nombre_carpeta}: {str(e)}")
                        self.log_signal.emit("error", f"❌ Error en {nombre_carpeta}: {str(e)}")

            self._finish_with_results()

        except Exception as e:
            error_msg = f"Error durante el proceso: {str(e)}"
            self.logger.error(error_msg)
            self.log_signal.emit("error", f"❌ {error_msg}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)

    def _handle_preflight_failure(self, preflight_report: dict):
        """Emite un bloqueo claro cuando falla la validacion previa."""
        blocking_issues = preflight_report.get('blocking_issues', [])
        missing_json_folders = [
            issue['folder_name']
            for issue in blocking_issues
            if issue.get('status') == 'missing_json'
        ]
        elapsed = time.time() - self.start_time

        self.time_update_signal.emit(elapsed)
        self.file_progress_signal.emit(0, 0)
        self.overall_progress_signal.emit(0)

        self.log_signal.emit("error", "❌ Validacion previa fallida. No se ejecutara el renombrado.")
        self.logger.error("❌ Validacion previa fallida. No se ejecutara el renombrado.")

        for issue in blocking_issues:
            msg = f"   • {issue['folder_name']}: {issue['message']}"
            self.log_signal.emit("error", msg)
            self.logger.error(msg)

        stats = {
            'lotes_procesados': 0,
            'total_exitosos': 0,
            'total_fallidos': len(blocking_issues),
            'total_omitidos': 0,
            'total_archivos': 0,
            'tiempo_transcurrido': elapsed,
            'detalle_por_lote': [],
            'preflight_report': preflight_report,
        }
        self.stats_signal.emit(stats)

        resultado = {
            'success': False,
            'preflight_ok': False,
            'preflight_report': preflight_report,
            'stats': stats,
            'totales': {
                'exitosos': 0,
                'fallidos': len(blocking_issues),
                'omitidos': 0,
                'archivos': 0,
            },
        }

        if missing_json_folders:
            folders_text = ", ".join(missing_json_folders)
            alert_message = (
                "Validacion previa fallida. Falta el JSON de renombrado en las "
                f"subcarpetas: {folders_text}."
            )
        else:
            blocking_folders = ", ".join(issue['folder_name'] for issue in blocking_issues)
            alert_message = (
                "Validacion previa fallida en el Paso 4. Revise las subcarpetas "
                f"bloqueadas: {blocking_folders}."
            )

        self.error_signal.emit(alert_message)
        self.finished_signal.emit(resultado)

    def _procesar_lote_paralelo(self, nombre_lote: str, carpeta_lote: str, ruta_json: str) -> dict:
        """Procesa un lote validado en paralelo usando el JSON aprobado por preflight."""
        try:
            self.folder_update_signal.emit(nombre_lote)

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

            exitosos, fallidos, omitidos, total = renombrar_archivos(carpeta_lote, mapeo)

            with self.files_lock:
                self.processed_files += total
                progress_percent = int((self.processed_files / self.total_files) * 100) if self.total_files > 0 else 0
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
        """Finaliza el proceso y emite resultados."""
        total_exitosos = sum(e['exitosos'] for e in self.estadisticas)
        total_fallidos = sum(e['fallidos'] for e in self.estadisticas)
        total_omitidos = sum(e['omitidos'] for e in self.estadisticas)
        total_archivos = sum(e['total'] for e in self.estadisticas)

        elapsed = time.time() - self.start_time
        self.time_update_signal.emit(elapsed)

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

        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self.log_signal.emit("info", f"⏱️ Tiempo total: {mins}m {secs}s")
        self.log_signal.emit("info", "=" * 50)

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

        stats = {
            'lotes_procesados': len(self.estadisticas),
            'total_exitosos': total_exitosos,
            'total_fallidos': total_fallidos,
            'total_omitidos': total_omitidos,
            'total_archivos': total_archivos,
            'tiempo_transcurrido': elapsed,
            'detalle_por_lote': self.estadisticas,
            'preflight_report': self.preflight_report,
        }
        self.stats_signal.emit(stats)

        resultado = {
            'success': True,
            'preflight_ok': True,
            'preflight_report': self.preflight_report,
            'stats': stats,
            'totales': {
                'exitosos': total_exitosos,
                'fallidos': total_fallidos,
                'omitidos': total_omitidos,
                'archivos': total_archivos,
            },
        }

        self.logger.info("🎉 ¡Renombrado completado exitosamente!")
        self.log_signal.emit("success", "🎉 ¡Renombrado completado exitosamente!")

        self.overall_progress_signal.emit(100)
        self.finished_signal.emit(resultado)

    def stop(self):
        """Detiene el worker."""
        self._is_running = False
        self.logger.warning("ℹ️ Worker detenido por el usuario")
