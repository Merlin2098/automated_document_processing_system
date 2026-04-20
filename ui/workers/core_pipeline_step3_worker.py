"""
Worker para generar diagnóstico de datos (Paso 3).
Incluye fallback seguro y diagnóstico estructurado para bundle.
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QThread, Signal

from utils.logger import Logger

# Agregar ruta del módulo core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_pipeline.step3_generar_diagnostico import (
    CARPETAS_CONFIG,
    procesar_diagnostico_a_excel,
)


def format_time(seconds: float) -> str:
    """Convierte segundos a formato hh:mm:ss."""
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
            archivos_pdf = [f for f in os.listdir(ruta_subcarpeta) if f.lower().endswith(".pdf")]
            count = len(archivos_pdf)
            por_carpeta[nombre_carpeta] = count
            total += count

    return {"total": total, "por_carpeta": por_carpeta}


class CorePipelineStep3Worker(QThread):
    """Worker para generar diagnóstico en segundo plano con fallback seguro."""

    progress_signal = Signal(int, int)
    log_signal = Signal(str, str)
    stats_signal = Signal(dict)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, folder_path: str, guardar_json: bool = False):
        super().__init__()
        self.folder_path = folder_path
        self.guardar_json = guardar_json
        self._is_running = True
        self.logger = Logger("CorePipelineStep3Worker")

        self.archivos_totales = 0
        self.archivos_procesados = 0
        self.carpetas_totales = 0
        self.carpetas_procesadas = 0
        self.errores_acumulados = 0

    def run(self):
        """Ejecuta el proceso de generación de diagnóstico con fallback."""
        start_time = time.time()
        timestamp = time.strftime("%d.%m.%Y_%H.%M.%S")
        nombre_excel = f"diagnostico_consolidado_{timestamp}.xlsx"
        ruta_excel = os.path.join(self.folder_path, nombre_excel)
        diagnostic_path = self._build_diagnostic_path(timestamp)
        attempts: List[Dict[str, Any]] = []

        try:
            self.logger.info("🚀 Worker: Iniciando diagnóstico optimizado")
            self.log_signal.emit("info", "🚀 Iniciando generación de diagnóstico (modo paralelo)...")

            conteo = contar_archivos_totales(self.folder_path)
            self.archivos_totales = conteo["total"]
            self.carpetas_totales = len(
                [carpeta for carpeta in CARPETAS_CONFIG.keys() if os.path.isdir(os.path.join(self.folder_path, carpeta))]
            )

            if self.carpetas_totales == 0:
                mensaje = "No se encontraron carpetas válidas para procesar"
                self._emit_failure(mensaje, diagnostic_path, attempts, start_time, ruta_excel)
                return

            self.logger.info(f"📂 Total: {self.archivos_totales} archivos en {self.carpetas_totales} carpetas")
            self.log_signal.emit(
                "info",
                f"📂 Total: {self.archivos_totales} archivos en {self.carpetas_totales} carpetas",
            )

            self._emit_stats(start_time)

            parallel_result = self._run_attempt(
                execution_mode="parallel",
                ruta_excel=ruta_excel,
                diagnostic_path=diagnostic_path,
                start_time=start_time,
            )
            attempts.append(parallel_result)

            final_result = parallel_result

            if not parallel_result.get("success", False) and self._is_running:
                self.log_signal.emit(
                    "warning",
                    "⚠️ El modo paralelo falló en bundle. Reintentando en modo seguro secuencial...",
                )
                self.logger.warning("⚠️ Falló el modo paralelo. Reintentando en modo secuencial.")

                self._reset_attempt_progress(start_time)

                sequential_result = self._run_attempt(
                    execution_mode="sequential",
                    ruta_excel=ruta_excel,
                    diagnostic_path=diagnostic_path,
                    start_time=start_time,
                )
                attempts.append(sequential_result)
                final_result = sequential_result

            self._write_diagnostic_file(
                diagnostic_path=diagnostic_path,
                requested_excel_path=ruta_excel,
                attempts=attempts,
                final_result=final_result,
                worker_started_at=start_time,
            )

            if not final_result.get("success", False):
                error_msg = final_result.get("error_message") or "No se pudo generar el diagnóstico"
                mensaje = f"{error_msg}. Diagnóstico: {diagnostic_path}"
                self.logger.error(f"❌ {mensaje}")
                self.log_signal.emit("error", f"❌ {mensaje}")
                self.error_signal.emit(mensaje)
                self.finished_signal.emit(
                    {
                        "success": False,
                        "error": error_msg,
                        "diagnostic_path": str(diagnostic_path),
                        "excel_path": ruta_excel,
                        "result": final_result,
                    }
                )
                return

            self.archivos_procesados = self.archivos_totales
            self.carpetas_procesadas = self.carpetas_totales
            self.progress_signal.emit(self.archivos_totales, self.archivos_totales)

            elapsed_time = time.time() - start_time
            time_formatted = format_time(elapsed_time)

            stats_final = {
                "current": self.archivos_totales,
                "total": self.archivos_totales,
                "time_elapsed": time_formatted,
                "carpetas_procesadas": self.carpetas_totales,
                "total_carpetas": self.carpetas_totales,
                "errors": self.errores_acumulados,
                "ruta_excel": ruta_excel,
                "diagnostic_path": str(diagnostic_path),
                "execution_mode": final_result.get("execution_mode"),
                "fallback_attempted": len(attempts) > 1,
            }
            self.stats_signal.emit(stats_final)

            resultado = {
                "success": True,
                "excel_path": ruta_excel,
                "diagnostic_path": str(diagnostic_path),
                "stats": stats_final,
                "carpetas_procesadas": self.carpetas_totales,
                "archivos_procesados": self.archivos_totales,
                "result": final_result,
            }

            self.logger.info(f"✅ Worker completado en {time_formatted}")
            if len(attempts) > 1:
                self.log_signal.emit(
                    "warning",
                    f"⚠️ Paso 3 se recuperó en modo seguro. Diagnóstico: {diagnostic_path.name}",
                )
            self.log_signal.emit("success", f"✅ Diagnóstico generado exitosamente en {time_formatted}")
            self.finished_signal.emit(resultado)

        except Exception as exc:
            final_result = {
                "success": False,
                "execution_mode": "worker_exception",
                "excel_path": ruta_excel,
                "diagnostic_path": str(diagnostic_path),
                "error_message": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "folder_summaries": [],
                "parquet_paths": {},
                "sheet_summaries": [],
                "excel_exists": False,
            }
            attempts.append(final_result)
            self._write_diagnostic_file(
                diagnostic_path=diagnostic_path,
                requested_excel_path=ruta_excel,
                attempts=attempts,
                final_result=final_result,
                worker_started_at=start_time,
            )
            mensaje = f"{final_result['error_message']}. Diagnóstico: {diagnostic_path}"
            self.logger.error(f"❌ {mensaje}")
            self.logger.error(final_result["traceback"])
            self.log_signal.emit("error", f"❌ {mensaje}")
            self.error_signal.emit(mensaje)
            self.finished_signal.emit(
                {
                    "success": False,
                    "error": final_result["error_message"],
                    "diagnostic_path": str(diagnostic_path),
                    "excel_path": ruta_excel,
                    "result": final_result,
                }
            )

    def _run_attempt(
        self,
        execution_mode: str,
        ruta_excel: str,
        diagnostic_path: Path,
        start_time: float,
    ) -> Dict[str, Any]:
        """Ejecuta un intento de generación en un modo específico."""
        self.log_signal.emit("info", f"🛠️ Paso 3 ejecutándose en modo: {execution_mode}")
        self.logger.info(f"🛠️ Ejecutando Paso 3 en modo {execution_mode}")

        def _progress_callback(carpetas_completadas: int, total_carpetas: int, summary: Dict[str, Any]) -> None:
            if not self._is_running:
                return

            self.carpetas_procesadas = carpetas_completadas
            self.archivos_procesados = min(
                self.archivos_procesados + int(summary.get("pdf_count", 0)),
                self.archivos_totales,
            )

            self.progress_signal.emit(self.archivos_procesados, self.archivos_totales)

            warnings_count = int(summary.get("warnings_count", 0))
            error_count = int(summary.get("error_count", 0))
            self.errores_acumulados += warnings_count + error_count

            for issue in summary.get("sample_issues", [])[:3]:
                issue_file = issue.get("file")
                issue_message = issue.get("message", "Sin detalle")
                if issue_file:
                    self.log_signal.emit("warning", f"⚠️ {issue_file}: {issue_message}")
                else:
                    self.log_signal.emit("warning", f"⚠️ {issue_message}")

            if summary.get("success", False):
                self.log_signal.emit(
                    "info",
                    (
                        f"📊 Carpeta {carpetas_completadas}/{total_carpetas} completada "
                        f"({summary.get('folder_name')}, {summary.get('row_count', 0)} registros)"
                    ),
                )
            else:
                self.log_signal.emit(
                    "error",
                    (
                        f"❌ Carpeta {summary.get('folder_name')} falló en modo {execution_mode}: "
                        f"{summary.get('error_message', 'Sin detalle')}"
                    ),
                )

            self._emit_stats(start_time)

        result = procesar_diagnostico_a_excel(
            ruta_carpeta_trabajo=self.folder_path,
            ruta_excel_final=ruta_excel,
            progress_callback=_progress_callback,
            guardar_json_opcional=self.guardar_json,
            execution_mode=execution_mode,
            diagnostic_path=str(diagnostic_path),
        )

        result["diagnostic_path"] = str(diagnostic_path)
        return result

    def _reset_attempt_progress(self, start_time: float) -> None:
        """Reinicia el progreso visual antes del fallback secuencial."""
        self.archivos_procesados = 0
        self.carpetas_procesadas = 0
        self.errores_acumulados = 0
        self.progress_signal.emit(0, self.archivos_totales)
        self._emit_stats(start_time)

    def _build_diagnostic_path(self, timestamp: str) -> Path:
        """Construye la ruta del diagnóstico Step 3 en logs/user."""
        diagnostic_dir = Path("logs") / "user"
        diagnostic_dir.mkdir(parents=True, exist_ok=True)
        return diagnostic_dir / f"step3_diagnostic_{timestamp}.json"

    def _write_diagnostic_file(
        self,
        diagnostic_path: Path,
        requested_excel_path: str,
        attempts: List[Dict[str, Any]],
        final_result: Dict[str, Any],
        worker_started_at: float,
    ) -> None:
        """Escribe el diagnóstico consolidado del Paso 3."""
        payload = {
            "selected_folder_path": self.folder_path,
            "requested_excel_path": requested_excel_path,
            "started_at": datetime.utcfromtimestamp(worker_started_at).isoformat(timespec="seconds") + "Z",
            "finished_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "frozen": getattr(sys, "frozen", False),
            "fallback_attempted": len(attempts) > 1,
            "initial_mode": attempts[0].get("execution_mode") if attempts else None,
            "final_mode": final_result.get("execution_mode"),
            "success": final_result.get("success", False),
            "pre_run_folder_counts": attempts[0].get("pre_run_folder_counts", {}) if attempts else {},
            "parquet_paths": final_result.get("parquet_paths", {}),
            "final_excel_exists": final_result.get("excel_exists", False),
            "error_message": final_result.get("error_message"),
            "traceback": final_result.get("traceback"),
            "attempts": [
                {
                    "execution_mode": attempt.get("execution_mode"),
                    "success": attempt.get("success", False),
                    "error_message": attempt.get("error_message"),
                    "excel_exists": attempt.get("excel_exists", False),
                    "started_at": attempt.get("started_at"),
                    "finished_at": attempt.get("finished_at"),
                    "folder_summaries": attempt.get("folder_summaries", []),
                    "sheet_summaries": attempt.get("sheet_summaries", []),
                    "parquet_paths": attempt.get("parquet_paths", {}),
                }
                for attempt in attempts
            ],
        }

        with diagnostic_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        self.logger.info(f"🧾 Diagnóstico Step 3 actualizado: {diagnostic_path}")

    def _emit_failure(
        self,
        error_msg: str,
        diagnostic_path: Path,
        attempts: List[Dict[str, Any]],
        start_time: float,
        ruta_excel: str,
    ) -> None:
        """Emite un fallo temprano y escribe diagnóstico mínimo."""
        final_result = {
            "success": False,
            "execution_mode": "preflight",
            "excel_path": ruta_excel,
            "diagnostic_path": str(diagnostic_path),
            "error_message": error_msg,
            "traceback": None,
            "folder_summaries": [],
            "parquet_paths": {},
            "sheet_summaries": [],
            "excel_exists": False,
            "pre_run_folder_counts": {},
        }
        attempts.append(final_result)
        self._write_diagnostic_file(
            diagnostic_path=diagnostic_path,
            requested_excel_path=ruta_excel,
            attempts=attempts,
            final_result=final_result,
            worker_started_at=start_time,
        )
        mensaje = f"{error_msg}. Diagnóstico: {diagnostic_path}"
        self.logger.error(f"❌ {mensaje}")
        self.log_signal.emit("error", f"❌ {mensaje}")
        self.error_signal.emit(mensaje)
        self.finished_signal.emit(
            {
                "success": False,
                "error": error_msg,
                "diagnostic_path": str(diagnostic_path),
                "excel_path": ruta_excel,
                "result": final_result,
            }
        )

    def _emit_stats(self, start_time: float) -> None:
        """Emite estadísticas actuales (compatible con UI)."""
        elapsed_time = time.time() - start_time
        time_formatted = format_time(elapsed_time)

        stats = {
            "current": self.archivos_procesados,
            "total": self.archivos_totales,
            "time_elapsed": time_formatted,
            "carpetas_procesadas": self.carpetas_procesadas,
            "total_carpetas": self.carpetas_totales,
            "errors": self.errores_acumulados,
        }
        self.stats_signal.emit(stats)

    def stop(self):
        """Detener el worker."""
        self.logger.warning("⚠️ Solicitud de detención recibida")
        self._is_running = False
        self.quit()
