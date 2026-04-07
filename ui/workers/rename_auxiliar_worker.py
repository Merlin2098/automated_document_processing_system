"""
Workers para Rename Auxiliar.
"""
from PySide6.QtCore import QThread, Signal
from utils.logger import Logger
import os
import sys
import time

# Agregar rutas para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core_pipeline.rename_auxiliar import (
    apply_single_folder_rename,
    prepare_single_folder_rename,
)


class RenameAuxiliarPreviewWorker(QThread):
    """Worker para generar vista previa de renombrado auxiliar."""

    preview_ready = Signal(dict)
    log_signal = Signal(str, str)
    stats_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, folder_path: str, json_path: str | None = None):
        super().__init__()
        self.folder_path = folder_path
        self.json_path = json_path or None
        self.logger = Logger("RenameAuxiliarPreview")

    def run(self):
        start_time = time.time()

        try:
            self.logger.info("🔍 Generando vista previa de renombrado auxiliar")
            self.log_signal.emit("info", "🔍 Generando vista previa de renombrado auxiliar")
            self.log_signal.emit("info", f"📂 Carpeta: {self.folder_path}")

            result = prepare_single_folder_rename(self.folder_path, self.json_path)
            elapsed = time.time() - start_time

            if not result["success"]:
                self.logger.error(result["message"])
                self.log_signal.emit("error", result["message"])

                if result.get("json_selection_required") and result.get("json_candidates"):
                    for candidate in result["json_candidates"]:
                        self.log_signal.emit("warning", f"JSON detectado: {os.path.basename(candidate)}")

                self.stats_signal.emit({"time": elapsed, "errors": 1})
                self.error_signal.emit(result["message"])
                return

            if result.get("json_sanitized"):
                self.log_signal.emit("warning", "Se aplico una correccion automatica al JSON.")

            if result.get("invalid_entries", 0) > 0:
                self.log_signal.emit(
                    "warning",
                    f"Se omitieron {result['invalid_entries']} registros invalidos del JSON.",
                )

            if result.get("duplicate_sources"):
                self.log_signal.emit(
                    "warning",
                    f"Se detectaron {len(result['duplicate_sources'])} archivos duplicados en el JSON. "
                    "Se uso la ultima ocurrencia.",
                )

            stats = result["stats"]
            mapping_count = result["mapping_count"]
            self.log_signal.emit("success", f"Vista previa lista: {mapping_count} registros evaluados.")
            self.log_signal.emit(
                "info",
                (
                    f"Resumen: {stats['ready']} listos, "
                    f"{stats['same_name']} sin cambio, "
                    f"{stats['target_exists']} ya existen, "
                    f"{stats['missing']} faltantes"
                ),
            )
            self.stats_signal.emit(
                {
                    "time": elapsed,
                    "errors": 0,
                    "current": mapping_count,
                    "total": mapping_count,
                }
            )
            self.preview_ready.emit(result)

        except Exception as exc:
            error_message = f"Error al generar la vista previa: {exc}"
            self.logger.error(error_message)
            self.log_signal.emit("error", error_message)
            self.error_signal.emit(error_message)


class RenameAuxiliarApplyWorker(QThread):
    """Worker para ejecutar el renombrado auxiliar."""

    progress_signal = Signal(int, int)
    log_signal = Signal(str, str)
    stats_signal = Signal(dict)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, folder_path: str, json_path: str):
        super().__init__()
        self.folder_path = folder_path
        self.json_path = json_path
        self.logger = Logger("RenameAuxiliarApply")
        self.start_time = None

    def run(self):
        self.start_time = time.time()

        try:
            self.logger.info("🚀 Iniciando renombrado auxiliar")
            self.log_signal.emit("info", "🚀 Iniciando renombrado auxiliar")
            self.log_signal.emit("info", f"📂 Carpeta: {self.folder_path}")
            self.log_signal.emit("info", f"🧾 JSON: {self.json_path}")

            def on_progress(current: int, total: int):
                self.progress_signal.emit(current, total)
                elapsed = time.time() - self.start_time
                self.stats_signal.emit(
                    {
                        "time": elapsed,
                        "errors": 0,
                        "current": current,
                        "total": total,
                    }
                )

            result = apply_single_folder_rename(
                self.folder_path,
                self.json_path,
                progress_callback=on_progress,
            )
            elapsed = time.time() - self.start_time

            if result["total"] == 0 and not result["success"]:
                self.logger.error(result["message"])
                self.log_signal.emit("error", result["message"])
                self.stats_signal.emit({"time": elapsed, "errors": 1})
                self.error_signal.emit(result["message"])
                return

            self.log_signal.emit("info", f"Total mapeado: {result['total']}")
            self.log_signal.emit("success", f"Renombrados: {result['renombrados']}")
            self.log_signal.emit("info", f"Omitidos: {result['omitidos']}")

            if result["fallidos"] > 0:
                self.log_signal.emit("error", f"Fallidos: {result['fallidos']}")
                for error in result["errors"][:10]:
                    self.log_signal.emit("error", error)
            else:
                self.log_signal.emit("success", "Renombrado completado sin errores.")

            self.stats_signal.emit(
                {
                    "time": elapsed,
                    "errors": result["fallidos"],
                    "current": result["total"],
                    "total": result["total"],
                }
            )
            self.finished_signal.emit(result)

        except Exception as exc:
            error_message = f"Error durante el renombrado auxiliar: {exc}"
            self.logger.error(error_message)
            self.log_signal.emit("error", error_message)
            self.error_signal.emit(error_message)
